import unittest
from unittest.mock import Mock

from elearn.controller import ApiController
from tests.world import STRONG, build_world


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.w = build_world()
        self.api = ApiController(self.w.users, self.w.courses, self.w.enrolments)

    def login(self, email, password=STRONG):
        return self.api.login(email, password, "test-client").body["token"]

    # ---- accounts ----
    def test_register_returns_201_and_never_exposes_the_password_hash(self):
        response = self.api.register("new@example.com", STRONG)
        self.assertEqual(response.status, 201)
        self.assertEqual(set(response.body), {"id", "email", "role"})

    def test_register_weak_password_returns_400_with_the_rules_listed(self):
        response = self.api.register("new@example.com", "abc")
        self.assertEqual(response.status, 400)
        self.assertIn("at least 10 characters", response.body["error"])

    def test_register_duplicate_returns_409(self):
        self.assertEqual(self.api.register("student@example.com", STRONG).status, 409)

    def test_login_success_returns_a_token(self):
        self.assertEqual(self.api.login("student@example.com", STRONG, "c").status, 200)

    def test_login_failure_returns_a_generic_401(self):
        wrong = self.api.login("student@example.com", "wrongpassword1", "c")
        unknown = self.api.login("nobody@example.com", STRONG, "c")
        self.assertEqual((wrong.status, unknown.status), (401, 401))
        self.assertEqual(wrong.body, unknown.body)

    def test_repeated_failures_return_429(self):
        for _ in range(5):
            self.api.login("student@example.com", "wrongpassword1", "c")
        self.assertEqual(self.api.login("student@example.com", STRONG, "c").status, 429)

    def test_logout_invalidates_the_token(self):
        token = self.login("student@example.com")
        self.assertEqual(self.api.logout(token).status, 200)
        self.assertEqual(self.api.my_courses(token).status, 401)

    def test_change_password_returns_200_and_revokes_the_session(self):
        token = self.login("student@example.com")
        self.assertEqual(self.api.change_password(token, STRONG, "newcorrecthorse7").status, 200)
        self.assertEqual(self.api.my_courses(token).status, 401)

    # ---- courses and enrolment, end to end ----
    def test_full_learning_journey(self):
        teacher = self.login("teacher@example.com")
        created = self.api.create_course(teacher, "Secure Coding", "Learn it", 10)
        self.assertEqual(created.status, 201)
        course_id = created.body["id"]
        self.assertEqual(self.api.list_courses().body["courses"], [])  # still a draft
        self.assertEqual(self.api.publish_course(teacher, course_id).status, 200)
        self.assertEqual(len(self.api.list_courses().body["courses"]), 1)
        self.assertEqual(len(self.api.search_courses("secure").body["courses"]), 1)

        student = self.login("student@example.com")
        self.assertEqual(self.api.enrol(student, course_id).status, 201)
        self.assertEqual(self.api.my_courses(student).body["courses"][0]["title"], "Secure Coding")
        self.assertEqual(self.api.roster(teacher, course_id).body["students"], ["student@example.com"])
        self.assertEqual(self.api.unenrol(student, course_id).status, 200)

    def test_unauthenticated_requests_return_401(self):
        for response in (self.api.create_course("bad-token", "Title", "d", 5),
                         self.api.enrol(None, 1), self.api.my_courses("x"), self.api.roster("x", 1)):
            self.assertEqual(response.status, 401)

    def test_wrong_role_returns_403(self):
        student = self.login("student@example.com")
        self.assertEqual(self.api.create_course(student, "Sneaky", "d", 5).status, 403)

    def test_unknown_course_returns_404(self):
        student = self.login("student@example.com")
        self.assertEqual(self.api.enrol(student, 9999).status, 404)

    def test_full_course_and_duplicate_enrolment_return_409(self):
        teacher = self.login("teacher@example.com")
        course_id = self.api.create_course(teacher, "Tiny Class", "d", 1).body["id"]
        self.api.publish_course(teacher, course_id)
        self.assertEqual(self.api.enrol(self.login("student@example.com"), course_id).status, 201)
        self.assertEqual(self.api.enrol(self.login("student@example.com"), course_id).status, 409)
        self.assertEqual(self.api.enrol(self.login("student2@example.com"), course_id).status, 409)

    def test_invalid_course_id_types_return_400_not_a_crash(self):
        student = self.login("student@example.com")
        for bad in ["1 OR 1=1", None, 1.5, True, [1]]:
            self.assertEqual(self.api.enrol(student, bad).status, 400, msg=repr(bad))

    def test_invalid_course_data_returns_400(self):
        teacher = self.login("teacher@example.com")
        self.assertEqual(self.api.create_course(teacher, "ab", "d", 5).status, 400)

    def test_unexpected_errors_return_a_generic_500_without_leaking_details(self):
        broken = Mock()
        broken.list_published.side_effect = RuntimeError("db password=hunter2 host=10.0.0.5")
        api = ApiController(self.w.users, broken, self.w.enrolments)
        response = api.list_courses()
        self.assertEqual(response.status, 500)
        self.assertNotIn("hunter2", str(response.body))


if __name__ == "__main__":
    unittest.main()
