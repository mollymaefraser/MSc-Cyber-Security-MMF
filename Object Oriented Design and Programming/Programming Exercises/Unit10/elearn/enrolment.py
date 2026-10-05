"""Enrolment Management module."""

import time
from dataclasses import dataclass
from typing import Callable, Optional

from .audit import AuditLog
from .courses import Course, CourseService
from .database import Database
from .errors import AuthorizationError, CourseFullError, EnrolmentError, NotFoundError
from .security import require_role
from .users import Role, SqliteUserRepository, User


@dataclass(frozen=True)
class Enrolment:
    course_id: int
    student_id: int
    enrolled_at: float


class SqliteEnrolmentRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def add(self, course_id: int, student_id: int, enrolled_at: float) -> Enrolment:
        """Check and insert in one transaction, so concurrent callers cannot overfill a course."""
        with self._db.transaction() as conn:
            row = conn.execute("SELECT capacity FROM courses WHERE id = ?", (course_id,)).fetchone()
            if row is None:
                raise NotFoundError("Course not found")
            if conn.execute("SELECT 1 FROM enrolments WHERE course_id = ? AND student_id = ?",
                            (course_id, student_id)).fetchone():
                raise EnrolmentError("Already enrolled in this course")
            taken = conn.execute("SELECT COUNT(*) FROM enrolments WHERE course_id = ?", (course_id,)).fetchone()[0]
            if taken >= row["capacity"]:
                raise CourseFullError("This course is full")
            conn.execute("INSERT INTO enrolments (course_id, student_id, enrolled_at) VALUES (?, ?, ?)",
                         (course_id, student_id, enrolled_at))
        return Enrolment(course_id, student_id, enrolled_at)

    def remove(self, course_id: int, student_id: int) -> bool:
        with self._db.transaction() as conn:
            cursor = conn.execute("DELETE FROM enrolments WHERE course_id = ? AND student_id = ?",
                                  (course_id, student_id))
        return cursor.rowcount == 1

    def course_rows_for_student(self, student_id: int) -> list:
        with self._db.transaction() as conn:
            return conn.execute(
                "SELECT c.* FROM courses c JOIN enrolments e ON e.course_id = c.id "
                "WHERE e.student_id = ? ORDER BY c.title COLLATE NOCASE, c.id", (student_id,)).fetchall()

    def student_ids_for_course(self, course_id: int) -> list:
        with self._db.transaction() as conn:
            rows = conn.execute("SELECT student_id FROM enrolments WHERE course_id = ?", (course_id,)).fetchall()
        return [r["student_id"] for r in rows]


class EnrolmentService:
    def __init__(self, repo: SqliteEnrolmentRepository, courses: CourseService,
                 users_repo: SqliteUserRepository, audit: Optional[AuditLog] = None,
                 clock: Callable[[], float] = time.time) -> None:
        self._repo = repo
        self._courses = courses
        self._users_repo = users_repo
        self._audit = audit or AuditLog()
        self._clock = clock

    def enrol(self, actor: User, course_id: int) -> Enrolment:
        require_role(actor, Role.STUDENT)
        self._courses.get_course(actor, course_id)  # hides drafts from students
        enrolment = self._repo.add(course_id, actor.id, self._clock())
        self._audit.record("student_enrolled", course_id=course_id, student_id=actor.id)
        return enrolment

    def unenrol(self, actor: User, course_id: int) -> None:
        require_role(actor, Role.STUDENT)
        if not self._repo.remove(course_id, actor.id):
            raise EnrolmentError("You are not enrolled in this course")
        self._audit.record("student_unenrolled", course_id=course_id, student_id=actor.id)

    def courses_for_student(self, actor: User) -> list:
        require_role(actor, Role.STUDENT)
        return [Course(r["id"], r["title"], r["description"], r["instructor_id"], r["capacity"],
                       bool(r["published"])) for r in self._repo.course_rows_for_student(actor.id)]

    def roster(self, actor: User, course_id: int) -> list:
        course = self._courses.get_course(actor, course_id)
        if not self._courses.can_manage(actor, course):
            raise AuthorizationError("Access denied")
        users = (self._users_repo.get(sid) for sid in self._repo.student_ids_for_course(course_id))
        return sorted(u.email for u in users if u)
