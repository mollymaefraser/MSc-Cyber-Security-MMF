"""End-to-end demonstration of the platform through the presentation layer."""

from elearn.audit import AuditLog
from elearn.controller import ApiController
from elearn.courses import CourseService, SqliteCourseRepository
from elearn.database import Database
from elearn.enrolment import EnrolmentService, SqliteEnrolmentRepository
from elearn.users import PasswordHasher, Role, SqliteUserRepository, UserService


def build_platform():
    db, audit = Database(), AuditLog()
    user_repo = SqliteUserRepository(db)
    users = UserService(user_repo, PasswordHasher(), audit=audit)
    courses = CourseService(SqliteCourseRepository(db), audit)
    enrolments = EnrolmentService(SqliteEnrolmentRepository(db), courses, user_repo, audit)
    return ApiController(users, courses, enrolments), users, audit


def show(label, response):
    print(f"{label:<52} -> {response.status} {response.body}")


if __name__ == "__main__":
    api, users, audit = build_platform()
    admin = users.bootstrap_admin("admin@school.example", "adminpassword-2026")
    teacher = users.set_role(admin, users.register("teacher@school.example", "teacherpass-2026").id, Role.INSTRUCTOR)

    print("--- Accounts and security checks ---")
    show("Register student", api.register("student@school.example", "correcthorse42"))
    show("Register with a weak password", api.register("weak@school.example", "abc"))
    show("Register the same email again", api.register("student@school.example", "correcthorse42"))
    show("Register with a SQL injection email", api.register("x'); DROP TABLE users;--@a.com", "correcthorse42"))
    show("Login with the wrong password", api.login("student@school.example", "wrong-password-1", "laptop"))
    teacher_token = api.login("teacher@school.example", "teacherpass-2026", "laptop").body["token"]
    student_token = api.login("student@school.example", "correcthorse42", "laptop").body["token"]

    print("\n--- Courses and enrolment ---")
    show("Student tries to create a course", api.create_course(student_token, "Hack", "d", 5))
    created = api.create_course(teacher_token, "Secure Software Engineering", "OO design and TDD", 2)
    show("Instructor creates a course", created)
    cid = created.body["id"]
    show("Student lists courses (draft is hidden)", api.list_courses())
    show("Instructor publishes the course", api.publish_course(teacher_token, cid))
    show("Student enrols", api.enrol(student_token, cid))
    show("Student enrols again", api.enrol(student_token, cid))
    show("Student requests the roster", api.roster(student_token, cid))
    show("Instructor requests the roster", api.roster(teacher_token, cid))
    show("Enrol with a malicious course id", api.enrol(student_token, "1 OR 1=1"))
    show("Use a forged token", api.my_courses("forged-token"))

    print("\n--- Brute force protection ---")
    for i in range(1, 7):
        show(f"Failed login attempt {i}", api.login("teacher@school.example", "wrong-password-1", "attacker"))

    print("\n--- Audit trail (no secrets recorded) ---")
    for name, fields in audit.events()[-4:]:
        print(f"{name}: {fields}")
