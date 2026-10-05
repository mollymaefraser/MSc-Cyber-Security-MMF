import unittest

from elearn.errors import AuthorizationError, NotFoundError, ValidationError
from tests.world import build_world


class CreateCourseTests(unittest.TestCase):
    def setUp(self):
        self.w = build_world()

    def test_instructor_creates_an_unpublished_course(self):
        course = self.w.courses.create_course(self.w.instructor, "Secure Coding", "Learn it", 30)
        self.assertEqual(course.title, "Secure Coding")
        self.assertEqual(course.instructor_id, self.w.instructor.id)
        self.assertEqual(course.capacity, 30)
        self.assertFalse(course.published)

    def test_admin_can_create_a_course(self):
        self.assertIsNotNone(self.w.courses.create_course(self.w.admin, "Admin Course", "d", 5).id)

    def test_student_cannot_create_a_course(self):
        with self.assertRaises(AuthorizationError):
            self.w.courses.create_course(self.w.student, "Sneaky", "d", 5)

    def test_title_is_trimmed(self):
        course = self.w.courses.create_course(self.w.instructor, "  Padded Title  ", "d", 5)
        self.assertEqual(course.title, "Padded Title")

    def test_invalid_titles_are_rejected(self):
        for bad in ["", "  ", "ab", "x" * 101, None, 123]:
            with self.assertRaises(ValidationError, msg=repr(bad)):
                self.w.courses.create_course(self.w.instructor, bad, "d", 5)

    def test_invalid_description_is_rejected(self):
        for bad in [None, 5, "x" * 2001]:
            with self.assertRaises(ValidationError, msg=repr(bad)):
                self.w.courses.create_course(self.w.instructor, "Valid Title", bad, 5)

    def test_invalid_capacities_are_rejected(self):
        for bad in [0, -1, 501, "10", 2.5, None, True]:
            with self.assertRaises(ValidationError, msg=repr(bad)):
                self.w.courses.create_course(self.w.instructor, "Valid Title", "d", bad)

    def test_creation_is_audited(self):
        self.w.courses.create_course(self.w.instructor, "Secure Coding", "d", 5)
        self.assertIn("course_created", [name for name, _ in self.w.audit.events()])


class PublishAndViewTests(unittest.TestCase):
    def setUp(self):
        self.w = build_world()
        self.course = self.w.courses.create_course(self.w.instructor, "Secure Coding", "d", 5)

    def test_owner_can_publish(self):
        self.assertTrue(self.w.courses.publish_course(self.w.instructor, self.course.id).published)

    def test_admin_can_publish_any_course(self):
        self.assertTrue(self.w.courses.publish_course(self.w.admin, self.course.id).published)

    def test_another_instructor_cannot_publish_it(self):
        with self.assertRaises(AuthorizationError):
            self.w.courses.publish_course(self.w.other_instructor, self.course.id)

    def test_student_cannot_publish(self):
        with self.assertRaises(AuthorizationError):
            self.w.courses.publish_course(self.w.student, self.course.id)

    def test_publishing_an_unknown_course_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.w.courses.publish_course(self.w.admin, 9999)

    def test_unpublished_course_is_hidden_from_students_and_other_instructors(self):
        for viewer in (self.w.student, self.w.other_instructor):
            with self.assertRaises(NotFoundError):
                self.w.courses.get_course(viewer, self.course.id)

    def test_unpublished_course_is_visible_to_owner_and_admin(self):
        for viewer in (self.w.instructor, self.w.admin):
            self.assertEqual(self.w.courses.get_course(viewer, self.course.id).id, self.course.id)

    def test_published_course_is_visible_to_students(self):
        self.w.courses.publish_course(self.w.instructor, self.course.id)
        self.assertEqual(self.w.courses.get_course(self.w.student, self.course.id).title, "Secure Coding")

    def test_unknown_course_raises_not_found_for_everyone(self):
        with self.assertRaises(NotFoundError):
            self.w.courses.get_course(self.w.admin, 9999)


class ListAndSearchTests(unittest.TestCase):
    def setUp(self):
        self.w = build_world()
        for title in ["Secure Coding", "Data Structures", "Secure Networks"]:
            course = self.w.courses.create_course(self.w.instructor, title, "d", 5)
            self.w.courses.publish_course(self.w.instructor, course.id)
        self.w.courses.create_course(self.w.instructor, "Hidden Draft", "d", 5)

    def test_list_published_excludes_drafts_and_is_sorted_by_title(self):
        titles = [c.title for c in self.w.courses.list_published()]
        self.assertEqual(titles, ["Data Structures", "Secure Coding", "Secure Networks"])

    def test_search_is_case_insensitive_substring_match(self):
        titles = [c.title for c in self.w.courses.search("SECURE")]
        self.assertEqual(titles, ["Secure Coding", "Secure Networks"])

    def test_search_never_returns_drafts(self):
        self.assertEqual(self.w.courses.search("Hidden"), [])

    def test_percent_and_underscore_are_treated_literally(self):
        self.assertEqual(self.w.courses.search("%"), [])
        self.assertEqual(self.w.courses.search("_"), [])

    def test_sql_injection_in_search_returns_nothing_and_tables_survive(self):
        self.assertEqual(self.w.courses.search("x' OR '1'='1"), [])
        self.assertEqual(len(self.w.courses.list_published()), 3)

    def test_invalid_search_term_is_rejected(self):
        for bad in [None, 5, "x" * 101]:
            with self.assertRaises(ValidationError, msg=repr(bad)):
                self.w.courses.search(bad)


if __name__ == "__main__":
    unittest.main()
