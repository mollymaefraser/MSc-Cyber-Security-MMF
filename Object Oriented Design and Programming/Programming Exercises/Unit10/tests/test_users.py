import unittest

from elearn.database import Database
from elearn.audit import AuditLog
from elearn.errors import (AuthenticationError, AuthorizationError, DuplicateEmailError, NotFoundError,
                           TooManyAttemptsError, ValidationError)
from elearn.users import (LOCKOUT_WINDOW_SECONDS, SESSION_TTL_SECONDS, CharacterMixRule,
                          CommonPasswordRule, LengthRule, PasswordHasher, PasswordPolicy, Role, SqliteUserRepository,
                          UserService)
from tests.helpers import FakeClock

STRONG = "correcthorse42"


def build_service(clock=None, audit=None):
    db = Database()
    repo = SqliteUserRepository(db)
    # A low scrypt cost keeps the suite fast. Production uses the default.
    service = UserService(repo, PasswordHasher(n=2 ** 10), clock=clock or FakeClock(), audit=audit)
    return service, db


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.service, self.db = build_service()

    def test_register_returns_a_student_with_an_id(self):
        user = self.service.register("molly@example.com", STRONG)
        self.assertIsInstance(user.id, int)
        self.assertEqual(user.email, "molly@example.com")
        self.assertEqual(user.role, Role.STUDENT)

    def test_email_is_normalised_to_lower_case_and_trimmed(self):
        user = self.service.register("  Molly@Example.COM ", STRONG)
        self.assertEqual(user.email, "molly@example.com")

    def test_duplicate_email_is_rejected_case_insensitively(self):
        self.service.register("molly@example.com", STRONG)
        with self.assertRaises(DuplicateEmailError):
            self.service.register("MOLLY@example.com", "anotherpass99")

    def test_invalid_emails_are_rejected(self):
        for bad in ["", "no-at-sign", "a@b", "two@@example.com", "sp ace@example.com", "x" * 300 + "@example.com"]:
            with self.assertRaises(ValidationError, msg=bad):
                self.service.register(bad, STRONG)

    def test_weak_passwords_are_rejected(self):
        for bad in ["short1", "alllettersnodigits", "1234567890123", "password123", ""]:
            with self.assertRaises(ValidationError, msg=bad):
                self.service.register("weak@example.com", bad)

    def test_very_long_password_is_rejected_to_prevent_hashing_abuse(self):
        with self.assertRaises(ValidationError):
            self.service.register("long@example.com", "a1" * 100)

    def test_password_is_never_stored_in_plain_text(self):
        self.service.register("molly@example.com", STRONG)
        with self.db.transaction() as conn:
            stored = conn.execute("SELECT password_hash FROM users").fetchone()["password_hash"]
        self.assertNotIn(STRONG, stored)
        self.assertTrue(stored.startswith("scrypt$"))

    def test_same_password_produces_different_hashes_because_of_salting(self):
        self.service.register("a@example.com", STRONG)
        self.service.register("b@example.com", STRONG)
        with self.db.transaction() as conn:
            hashes = [r["password_hash"] for r in conn.execute("SELECT password_hash FROM users")]
        self.assertNotEqual(hashes[0], hashes[1])

    def test_sql_injection_in_email_is_rejected_and_tables_survive(self):
        with self.assertRaises(ValidationError):
            self.service.register("x'); DROP TABLE users;--@example.com", STRONG)
        self.service.register("still-works@example.com", STRONG)


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.service, self.db = build_service(self.clock)
        self.user = self.service.register("molly@example.com", STRONG)

    def test_login_returns_a_token_that_resolves_to_the_user(self):
        token = self.service.authenticate("molly@example.com", STRONG)
        self.assertEqual(self.service.user_for_token(token), self.user)

    def test_login_is_case_insensitive_on_email(self):
        token = self.service.authenticate("MOLLY@Example.com", STRONG)
        self.assertEqual(self.service.user_for_token(token).id, self.user.id)

    def test_wrong_password_is_rejected(self):
        with self.assertRaises(AuthenticationError):
            self.service.authenticate("molly@example.com", "wrongpassword1")

    def test_unknown_user_gets_the_same_error_as_a_wrong_password(self):
        with self.assertRaises(AuthenticationError) as unknown:
            self.service.authenticate("nobody@example.com", STRONG)
        with self.assertRaises(AuthenticationError) as wrong:
            self.service.authenticate("molly@example.com", "wrongpassword1")
        self.assertEqual(str(unknown.exception), str(wrong.exception))

    def test_non_string_credentials_are_rejected_cleanly(self):
        for bad in [None, 123, b"bytes"]:
            with self.assertRaises(AuthenticationError, msg=repr(bad)):
                self.service.authenticate(bad, bad)

    def test_tokens_are_unique_and_unguessably_long(self):
        first = self.service.authenticate("molly@example.com", STRONG)
        second = self.service.authenticate("molly@example.com", STRONG)
        self.assertNotEqual(first, second)
        self.assertGreaterEqual(len(first), 40)

    def test_session_expires_after_the_time_to_live(self):
        token = self.service.authenticate("molly@example.com", STRONG)
        self.clock.advance(SESSION_TTL_SECONDS + 1)
        with self.assertRaises(AuthenticationError):
            self.service.user_for_token(token)

    def test_session_is_still_valid_just_before_expiry(self):
        token = self.service.authenticate("molly@example.com", STRONG)
        self.clock.advance(SESSION_TTL_SECONDS - 1)
        self.assertEqual(self.service.user_for_token(token).id, self.user.id)

    def test_logout_invalidates_the_token(self):
        token = self.service.authenticate("molly@example.com", STRONG)
        self.service.logout(token)
        with self.assertRaises(AuthenticationError):
            self.service.user_for_token(token)

    def test_forged_and_malformed_tokens_are_rejected(self):
        for bad in ["forged-token", "", None, 42]:
            with self.assertRaises(AuthenticationError, msg=repr(bad)):
                self.service.user_for_token(bad)

    def test_session_tokens_are_not_stored_in_plain_text(self):
        token = self.service.authenticate("molly@example.com", STRONG)
        self.assertNotIn(token, self.service._sessions._sessions)


class EdgeCaseTests(unittest.TestCase):
    """Edge cases found by reviewing the coverage report for unexercised branches."""

    def setUp(self):
        self.service, self.db = build_service()
        self.service.register("molly@example.com", STRONG)

    def test_malformed_email_at_login_is_an_authentication_failure_not_a_validation_leak(self):
        with self.assertRaises(AuthenticationError):
            self.service.authenticate("not-an-email", STRONG)

    def test_non_text_email_at_registration_is_rejected(self):
        for bad in [None, 42, b"a@b.com"]:
            with self.assertRaises(ValidationError, msg=repr(bad)):
                self.service.register(bad, STRONG)

    def test_session_for_a_deleted_account_is_rejected(self):
        token = self.service.authenticate("molly@example.com", STRONG)
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM users")
        with self.assertRaises(AuthenticationError):
            self.service.user_for_token(token)


class PasswordPolicyTests(unittest.TestCase):
    """Added during the refactor step: the policy is now a set of interchangeable rules."""

    def test_default_policy_accepts_a_strong_password(self):
        PasswordPolicy.default().validate(STRONG)

    def test_policy_reports_every_violation_not_just_the_first(self):
        with self.assertRaises(ValidationError) as ctx:
            PasswordPolicy.default().validate("abc")
        self.assertEqual(len(ctx.exception.args[0]), 2)  # too short and no digit

    def test_length_rule_enforces_both_bounds(self):
        rule = LengthRule(minimum=10, maximum=20)
        self.assertIsNotNone(rule.check("short1"))
        self.assertIsNotNone(rule.check("a1" * 11))
        self.assertIsNone(rule.check("a1" * 5))

    def test_character_mix_rule_needs_a_letter_and_a_digit(self):
        rule = CharacterMixRule()
        self.assertIsNotNone(rule.check("onlyletters"))
        self.assertIsNotNone(rule.check("1234567890"))
        self.assertIsNone(rule.check("letters123"))

    def test_common_password_rule_is_case_insensitive(self):
        self.assertIsNotNone(CommonPasswordRule({"password123"}).check("PassWord123"))

    def test_non_string_password_is_rejected(self):
        for bad in [None, 123, b"bytes"]:
            with self.assertRaises(ValidationError, msg=repr(bad)):
                PasswordPolicy.default().validate(bad)

    def test_custom_policy_can_be_composed_from_rules(self):
        strict = PasswordPolicy([LengthRule(minimum=16, maximum=128), CharacterMixRule()])
        with self.assertRaises(ValidationError):
            strict.validate(STRONG)  # 14 characters


class LoginThrottleTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.service, _ = build_service(self.clock)
        self.service.register("molly@example.com", STRONG)

    def fail(self, times, client="client-a"):
        for _ in range(times):
            with self.assertRaises(AuthenticationError):
                self.service.authenticate("molly@example.com", "wrongpassword1", client)

    def test_client_is_locked_out_after_five_failures_even_with_the_right_password(self):
        self.fail(5)
        with self.assertRaises(TooManyAttemptsError):
            self.service.authenticate("molly@example.com", STRONG, "client-a")

    def test_lockout_expires_after_the_window(self):
        self.fail(5)
        self.clock.advance(LOCKOUT_WINDOW_SECONDS + 1)
        self.assertIsInstance(self.service.authenticate("molly@example.com", STRONG, "client-a"), str)

    def test_lockout_is_scoped_to_the_client_not_global(self):
        self.fail(5, "client-a")
        self.assertIsInstance(self.service.authenticate("molly@example.com", STRONG, "client-b"), str)

    def test_successful_login_resets_the_failure_count(self):
        self.fail(4)
        self.service.authenticate("molly@example.com", STRONG, "client-a")
        self.fail(4)  # would have locked out at five without the reset
        self.assertIsInstance(self.service.authenticate("molly@example.com", STRONG, "client-a"), str)


class ChangePasswordTests(unittest.TestCase):
    def setUp(self):
        self.service, _ = build_service()
        self.user = self.service.register("molly@example.com", STRONG)

    def test_new_password_works_and_old_password_stops_working(self):
        self.service.change_password(self.user.id, STRONG, "newcorrecthorse7")
        self.assertIsInstance(self.service.authenticate("molly@example.com", "newcorrecthorse7"), str)
        with self.assertRaises(AuthenticationError):
            self.service.authenticate("molly@example.com", STRONG)

    def test_wrong_current_password_is_rejected(self):
        with self.assertRaises(AuthenticationError):
            self.service.change_password(self.user.id, "wrongpassword1", "newcorrecthorse7")

    def test_weak_new_password_is_rejected_and_old_one_still_works(self):
        with self.assertRaises(ValidationError):
            self.service.change_password(self.user.id, STRONG, "weak")
        self.assertIsInstance(self.service.authenticate("molly@example.com", STRONG), str)

    def test_changing_password_revokes_existing_sessions(self):
        token = self.service.authenticate("molly@example.com", STRONG)
        self.service.change_password(self.user.id, STRONG, "newcorrecthorse7")
        with self.assertRaises(AuthenticationError):
            self.service.user_for_token(token)


class RoleManagementTests(unittest.TestCase):
    def setUp(self):
        self.service, _ = build_service()
        self.admin = self.service.bootstrap_admin("admin@example.com", STRONG)
        self.student = self.service.register("student@example.com", STRONG)

    def test_bootstrap_admin_creates_an_admin(self):
        self.assertEqual(self.admin.role, Role.ADMIN)

    def test_admin_can_promote_a_student_to_instructor(self):
        updated = self.service.set_role(self.admin, self.student.id, Role.INSTRUCTOR)
        self.assertEqual(updated.role, Role.INSTRUCTOR)
        token = self.service.authenticate("student@example.com", STRONG)
        self.assertEqual(self.service.user_for_token(token).role, Role.INSTRUCTOR)

    def test_a_student_cannot_promote_themselves(self):
        with self.assertRaises(AuthorizationError):
            self.service.set_role(self.student, self.student.id, Role.ADMIN)

    def test_promoting_an_unknown_user_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.service.set_role(self.admin, 9999, Role.INSTRUCTOR)

    def test_invalid_role_value_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.service.set_role(self.admin, self.student.id, "superuser")


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.audit = AuditLog()
        self.service, _ = build_service(audit=self.audit)

    def test_registration_and_failed_login_are_recorded(self):
        self.service.register("molly@example.com", STRONG)
        with self.assertRaises(AuthenticationError):
            self.service.authenticate("molly@example.com", "wrongpassword1", "client-a")
        names = [name for name, _ in self.audit.events()]
        self.assertEqual(names, ["user_registered", "login_failed"])

    def test_lockout_is_recorded_in_the_audit_log(self):
        self.service.register("molly@example.com", STRONG)
        for _ in range(5):
            with self.assertRaises(AuthenticationError):
                self.service.authenticate("molly@example.com", "wrongpassword1", "client-a")
        with self.assertRaises(TooManyAttemptsError):
            self.service.authenticate("molly@example.com", STRONG, "client-a")
        self.assertEqual(self.audit.events()[-1][0], "login_locked_out")

    def test_audit_log_never_contains_passwords(self):
        self.service.register("molly@example.com", STRONG)
        with self.assertRaises(AuthenticationError):
            self.service.authenticate("molly@example.com", "wrongpassword1", "client-a")
        self.assertNotIn(STRONG, str(self.audit.events()))
        self.assertNotIn("wrongpassword1", str(self.audit.events()))


if __name__ == "__main__":
    unittest.main()
