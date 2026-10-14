"""Shared fixture: a fully wired platform with one admin, one instructor and two students."""

from types import SimpleNamespace

from elearn.audit import AuditLog
from elearn.courses import CourseService, SqliteCourseRepository
from elearn.database import Database
from elearn.enrolment import EnrolmentService, SqliteEnrolmentRepository
from elearn.users import PasswordHasher, Role, SqliteUserRepository, UserService
from tests.helpers import FakeClock

STRONG = "correcthorse42"


def build_world():
    clock = FakeClock()
    audit = AuditLog()
    db = Database()
    users = UserService(SqliteUserRepository(db), PasswordHasher(n=2 ** 10), clock=clock, audit=audit)
    courses = CourseService(SqliteCourseRepository(db), audit)
    enrolments = EnrolmentService(SqliteEnrolmentRepository(db), courses, users_repo=SqliteUserRepository(db),
                                  audit=audit, clock=clock)
    admin = users.bootstrap_admin("admin@example.com", STRONG)
    instructor = users.set_role(admin, users.register("teacher@example.com", STRONG).id, Role.INSTRUCTOR)
    other_instructor = users.set_role(admin, users.register("teacher2@example.com", STRONG).id, Role.INSTRUCTOR)
    student = users.register("student@example.com", STRONG)
    student2 = users.register("student2@example.com", STRONG)
    return SimpleNamespace(clock=clock, audit=audit, db=db, users=users, courses=courses,
                           enrolments=enrolments, admin=admin, instructor=instructor,
                           other_instructor=other_instructor, student=student, student2=student2)
