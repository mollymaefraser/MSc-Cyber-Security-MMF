import threading
import unittest

from elearn.errors import (AuthorisationError, CourseFullError, EnrolmentError, NotFoundError)
from tests.world import STRONG, build_world


class EnrolTests(unittest.TestCase):
    def setUp(self):
        self.w = build_world()
        self.course = self.w.courses.create_course(self.w.instructor, "Secure Coding", "d", 2)
        self.w.courses.publish_course(self.w.instructor, self.course.id)

    def test_student_can_enrol_in_a_published_course(self):
        enrolment = self.w.enrolments.enrol(self.w.student, self.course.id)
        self.assertEqual(enrolment.course_id, self.course.id)
        self.assertEqual(enrolment.student_id, self.w.student.id)

    def test_instructors_and_admins_cannot_enrol(self):
        for actor in (self.w.instructor, self.w.admin):
            with self.assertRaises(AuthorisationError):
                self.w.enrolments.enrol(actor, self.course.id)

    def test_cannot_enrol_in_an_unpublished_course(self):
        draft = self.w.courses.create_course(self.w.instructor, "Draft Course", "d", 5)
        with self.assertRaises(NotFoundError):
            self.w.enrolments.enrol(self.w.student, draft.id)

    def test_cannot_enrol_in_an_unknown_course(self):
        with self.assertRaises(NotFoundError):
            self.w.enrolments.enrol(self.w.student, 9999)

    def test_enrolling_twice_is_rejected(self):
        self.w.enrolments.enrol(self.w.student, self.course.id)
        with self.assertRaises(EnrolmentError):
            self.w.enrolments.enrol(self.w.student, self.course.id)

    def test_full_course_rejects_further_students(self):
        extra = [self.w.users.register(f"extra{i}@example.com", STRONG) for i in range(2)]
        self.w.enrolments.enrol(self.w.student, self.course.id)
        self.w.enrolments.enrol(extra[0], self.course.id)
        with self.assertRaises(CourseFullError):
            self.w.enrolments.enrol(extra[1], self.course.id)

    def test_a_place_is_freed_when_a_student_unenrols(self):
        extra = [self.w.users.register(f"extra{i}@example.com", STRONG) for i in range(2)]
        self.w.enrolments.enrol(self.w.student, self.course.id)
        self.w.enrolments.enrol(extra[0], self.course.id)
        self.w.enrolments.unenrol(self.w.student, self.course.id)
        self.w.enrolments.enrol(extra[1], self.course.id)  # must now succeed

    def test_enrolment_is_audited(self):
        self.w.enrolments.enrol(self.w.student, self.course.id)
        self.assertIn("student_enrolled", [name for name, _ in self.w.audit.events()])


class UnenrolTests(unittest.TestCase):
    def setUp(self):
        self.w = build_world()
        self.course = self.w.courses.create_course(self.w.instructor, "Secure Coding", "d", 5)
        self.w.courses.publish_course(self.w.instructor, self.course.id)

    def test_unenrol_removes_the_enrolment(self):
        self.w.enrolments.enrol(self.w.student, self.course.id)
        self.w.enrolments.unenrol(self.w.student, self.course.id)
        self.assertEqual(self.w.enrolments.courses_for_student(self.w.student), [])

    def test_unenrolling_when_not_enrolled_is_rejected(self):
        with self.assertRaises(EnrolmentError):
            self.w.enrolments.unenrol(self.w.student, self.course.id)

    def test_non_students_cannot_unenrol(self):
        with self.assertRaises(AuthorisationError):
            self.w.enrolments.unenrol(self.w.instructor, self.course.id)


class CoursesForStudentTests(unittest.TestCase):
    def setUp(self):
        self.w = build_world()
        self.courses = []
        for title in ["Zoology Basics", "Algorithms"]:
            course = self.w.courses.create_course(self.w.instructor, title, "d", 5)
            self.w.courses.publish_course(self.w.instructor, course.id)
            self.courses.append(course)

    def test_returns_only_the_students_own_courses_sorted_by_title(self):
        for course in self.courses:
            self.w.enrolments.enrol(self.w.student, course.id)
        self.w.enrolments.enrol(self.w.student2, self.courses[0].id)
        titles = [c.title for c in self.w.enrolments.courses_for_student(self.w.student)]
        self.assertEqual(titles, ["Algorithms", "Zoology Basics"])
        self.assertEqual(len(self.w.enrolments.courses_for_student(self.w.student2)), 1)

    def test_non_students_are_denied(self):
        with self.assertRaises(AuthorisationError):
            self.w.enrolments.courses_for_student(self.w.instructor)


class RosterTests(unittest.TestCase):
    def setUp(self):
        self.w = build_world()
        self.course = self.w.courses.create_course(self.w.instructor, "Secure Coding", "d", 5)
        self.w.courses.publish_course(self.w.instructor, self.course.id)
        self.w.enrolments.enrol(self.w.student2, self.course.id)
        self.w.enrolments.enrol(self.w.student, self.course.id)

    def test_owner_sees_the_roster_sorted_by_email(self):
        self.assertEqual(self.w.enrolments.roster(self.w.instructor, self.course.id),
                         ["student2@example.com", "student@example.com"])

    def test_admin_sees_the_roster(self):
        self.assertEqual(len(self.w.enrolments.roster(self.w.admin, self.course.id)), 2)

    def test_other_instructors_and_students_are_denied(self):
        for actor in (self.w.other_instructor, self.w.student):
            with self.assertRaises(AuthorisationError):
                self.w.enrolments.roster(actor, self.course.id)

    def test_unknown_course_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.w.enrolments.roster(self.w.admin, 9999)


class ConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.w = build_world()
        self.course = self.w.courses.create_course(self.w.instructor, "Last Seat", "d", 1)
        self.w.courses.publish_course(self.w.instructor, self.course.id)

    def run_threads(self, targets):
        results = []
        lock = threading.Lock()

        def runner(fn):
            try:
                fn()
                outcome = "ok"
            except CourseFullError:
                outcome = "full"
            except EnrolmentError:
                outcome = "duplicate"
            with lock:
                results.append(outcome)

        threads = [threading.Thread(target=runner, args=(t,)) for t in targets]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return results

    def test_ten_students_racing_for_the_last_seat_yield_exactly_one_winner(self):
        students = [self.w.users.register(f"racer{i}@example.com", STRONG) for i in range(10)]
        results = self.run_threads([lambda s=s: self.w.enrolments.enrol(s, self.course.id) for s in students])
        self.assertEqual(results.count("ok"), 1)
        self.assertEqual(results.count("full"), 9)
        self.assertEqual(len(self.w.enrolments.roster(self.w.admin, self.course.id)), 1)

    def test_one_student_enrolling_ten_times_at_once_is_enrolled_once(self):
        results = self.run_threads([lambda: self.w.enrolments.enrol(self.w.student, self.course.id)] * 10)
        self.assertEqual(results.count("ok"), 1)
        self.assertEqual(len(self.w.enrolments.roster(self.w.admin, self.course.id)), 1)


if __name__ == "__main__":
    unittest.main()
