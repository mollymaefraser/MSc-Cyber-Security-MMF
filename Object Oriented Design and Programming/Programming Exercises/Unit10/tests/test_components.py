"""Direct unit tests for the lower-level building blocks (hasher, sessions, throttle, repositories)."""

import unittest

from elearn.audit import AuditLog
from elearn.courses import CourseService, SqliteCourseRepository
from elearn.database import Database
from elearn.enrolment import SqliteEnrolmentRepository
from elearn.errors import (AuthenticationError, CourseFullError, DuplicateEmailError, EnrolmentError,
                           NotFoundError, TooManyAttemptsError)
from elearn.users import (LoginThrottle, PasswordHasher, PasswordRule, Role, SessionManager,
                          SqliteUserRepository, User)
from tests.helpers import FakeClock
from tests.world import build_world


class PasswordHasherTests(unittest.TestCase):
    def setUp(self):
        self.hasher = PasswordHasher(n=2 ** 10)

    def test_hash_then_verify_round_trips(self):
        self.assertTrue(self.hasher.verify("correcthorse42", self.hasher.hash("correcthorse42")))

    def test_verify_rejects_the_wrong_password(self):
        self.assertFalse(self.hasher.verify("wrong", self.hasher.hash("correcthorse42")))

    def test_verify_rejects_malformed_stored_values_instead_of_crashing(self):
        for bad in ["", "plaintext", "scrypt$x$y$z", "a$b$c", None]:
            self.assertFalse(self.hasher.verify("anything", bad), msg=repr(bad))

    def test_hash_records_the_cost_parameter_so_it_can_be_raised_later(self):
        stored = self.hasher.hash("correcthorse42")
        self.assertEqual(stored.split("$")[1], str(2 ** 10))
        # a hash made at one cost still verifies on a hasher configured with another
        self.assertTrue(PasswordHasher(n=2 ** 12).verify("correcthorse42", stored))


class PasswordRuleTests(unittest.TestCase):
    def test_base_rule_is_abstract(self):
        with self.assertRaises(NotImplementedError):
            PasswordRule().check("x")


class SessionManagerTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.sessions = SessionManager(self.clock, ttl=60)

    def test_create_then_resolve_returns_the_user_id(self):
        self.assertEqual(self.sessions.resolve(self.sessions.create(7)), 7)

    def test_resolve_rejects_expired_sessions_and_removes_them(self):
        token = self.sessions.create(7)
        self.clock.advance(61)
        with self.assertRaises(AuthenticationError):
            self.sessions.resolve(token)
        self.assertEqual(self.sessions._sessions, {})

    def test_revoke_removes_only_that_session(self):
        first, second = self.sessions.create(7), self.sessions.create(7)
        self.sessions.revoke(first)
        with self.assertRaises(AuthenticationError):
            self.sessions.resolve(first)
        self.assertEqual(self.sessions.resolve(second), 7)

    def test_revoke_ignores_garbage_input(self):
        self.sessions.revoke(None)
        self.sessions.revoke(123)

    def test_revoke_all_for_user_leaves_other_users_alone(self):
        mine, theirs = self.sessions.create(1), self.sessions.create(2)
        self.sessions.revoke_all_for_user(1)
        with self.assertRaises(AuthenticationError):
            self.sessions.resolve(mine)
        self.assertEqual(self.sessions.resolve(theirs), 2)


class LoginThrottleTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.throttle = LoginThrottle(self.clock, max_failures=3, window=60)
        self.key = ("client", "a@example.com")

    def test_check_passes_until_the_limit_is_reached(self):
        for _ in range(2):
            self.throttle.record_failure(self.key)
        self.throttle.check(self.key)
        self.throttle.record_failure(self.key)
        with self.assertRaises(TooManyAttemptsError):
            self.throttle.check(self.key)

    def test_old_failures_age_out_of_the_window(self):
        for _ in range(3):
            self.throttle.record_failure(self.key)
        self.clock.advance(61)
        self.throttle.check(self.key)
        self.assertNotIn(self.key, self.throttle._failures)

    def test_reset_clears_the_count(self):
        for _ in range(3):
            self.throttle.record_failure(self.key)
        self.throttle.reset(self.key)
        self.throttle.check(self.key)

    def test_keys_are_independent(self):
        for _ in range(3):
            self.throttle.record_failure(self.key)
        self.throttle.check(("other-client", "a@example.com"))


class UserRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.repo = SqliteUserRepository(Database())

    def test_add_then_find_and_get(self):
        user = self.repo.add("a@example.com", "hash-a", Role.STUDENT, 1.0)
        self.assertEqual(self.repo.get(user.id), user)
        self.assertEqual(self.repo.find_by_email("a@example.com"), (user, "hash-a"))
        self.assertEqual(self.repo.get_with_hash(user.id), (user, "hash-a"))

    def test_lookups_return_none_when_missing(self):
        self.assertIsNone(self.repo.get(99))
        self.assertIsNone(self.repo.find_by_email("nobody@example.com"))
        self.assertIsNone(self.repo.get_with_hash(99))

    def test_add_rejects_duplicates_with_a_domain_error(self):
        self.repo.add("a@example.com", "h", Role.STUDENT, 1.0)
        with self.assertRaises(DuplicateEmailError):
            self.repo.add("a@example.com", "h2", Role.STUDENT, 2.0)

    def test_update_password_hash(self):
        user = self.repo.add("a@example.com", "old", Role.STUDENT, 1.0)
        self.repo.update_password_hash(user.id, "new")
        self.assertEqual(self.repo.find_by_email("a@example.com")[1], "new")

    def test_update_role_reports_whether_a_row_changed(self):
        user = self.repo.add("a@example.com", "h", Role.STUDENT, 1.0)
        self.assertTrue(self.repo.update_role(user.id, Role.ADMIN))
        self.assertEqual(self.repo.get(user.id).role, Role.ADMIN)
        self.assertFalse(self.repo.update_role(99, Role.ADMIN))

    def test_database_rejects_an_invalid_role_even_if_the_application_layer_is_bypassed(self):
        import sqlite3
        db = Database()
        with self.assertRaises(sqlite3.IntegrityError):
            with db.transaction() as conn:
                conn.execute("INSERT INTO users (email, password_hash, role, created_at) "
                             "VALUES ('x@example.com', 'h', 'superuser', 0)")


class CourseRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.w = build_world()
        self.repo = SqliteCourseRepository(self.w.db)

    def test_add_get_and_publish(self):
        course = self.repo.add("Title", "Desc", self.w.instructor.id, 5)
        self.assertFalse(self.repo.get(course.id).published)
        self.repo.set_published(course.id)
        self.assertTrue(self.repo.get(course.id).published)

    def test_get_returns_none_when_missing(self):
        self.assertIsNone(self.repo.get(99))

    def test_search_published_ignores_drafts(self):
        published = self.repo.add("Python Basics", "d", self.w.instructor.id, 5)
        self.repo.add("Python Draft", "d", self.w.instructor.id, 5)
        self.repo.set_published(published.id)
        self.assertEqual([c.title for c in self.repo.search_published("python")], ["Python Basics"])

    def test_database_rejects_an_out_of_range_capacity_even_if_validation_is_bypassed(self):
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.add("Title", "d", self.w.instructor.id, 0)

    def test_database_rejects_a_course_for_a_nonexistent_instructor(self):
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.add("Title", "d", 9999, 5)


class CourseServiceHelperTests(unittest.TestCase):
    def test_can_manage_covers_owner_admin_and_everyone_else(self):
        w = build_world()
        course = w.courses.create_course(w.instructor, "Secure Coding", "d", 5)
        self.assertTrue(CourseService.can_manage(w.instructor, course))
        self.assertTrue(CourseService.can_manage(w.admin, course))
        self.assertFalse(CourseService.can_manage(w.other_instructor, course))
        self.assertFalse(CourseService.can_manage(w.student, course))


class EnrolmentRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.w = build_world()
        self.course = self.w.courses.create_course(self.w.instructor, "Secure Coding", "d", 1)
        self.repo = SqliteEnrolmentRepository(self.w.db)

    def test_add_and_list(self):
        self.repo.add(self.course.id, self.w.student.id, 5.0)
        self.assertEqual(self.repo.student_ids_for_course(self.course.id), [self.w.student.id])
        self.assertEqual(self.repo.course_rows_for_student(self.w.student.id)[0]["title"], "Secure Coding")

    def test_add_enforces_capacity_duplicates_and_existence(self):
        self.repo.add(self.course.id, self.w.student.id, 5.0)
        with self.assertRaises(EnrolmentError):
            self.repo.add(self.course.id, self.w.student.id, 6.0)
        with self.assertRaises(CourseFullError):
            self.repo.add(self.course.id, self.w.student2.id, 6.0)
        with self.assertRaises(NotFoundError):
            self.repo.add(9999, self.w.student.id, 6.0)

    def test_remove_reports_whether_a_row_was_deleted(self):
        self.repo.add(self.course.id, self.w.student.id, 5.0)
        self.assertTrue(self.repo.remove(self.course.id, self.w.student.id))
        self.assertFalse(self.repo.remove(self.course.id, self.w.student.id))


class AuditLogTests(unittest.TestCase):
    def test_events_are_returned_in_order_as_a_copy(self):
        audit = AuditLog()
        audit.record("first", a=1)
        audit.record("second")
        events = audit.events()
        self.assertEqual(events, [("first", {"a": 1}), ("second", {})])
        events.clear()
        self.assertEqual(len(audit.events()), 2)  # callers cannot tamper with the log


if __name__ == "__main__":
    unittest.main()
