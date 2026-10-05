"""Course Management module."""

from dataclasses import dataclass
from typing import Optional

from .audit import AuditLog
from .database import Database
from .errors import AuthorizationError, NotFoundError, ValidationError
from .security import require_role
from .users import Role, User


@dataclass(frozen=True)
class Course:
    id: int
    title: str
    description: str
    instructor_id: int
    capacity: int
    published: bool


class SqliteCourseRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def add(self, title: str, description: str, instructor_id: int, capacity: int) -> Course:
        with self._db.transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO courses (title, description, instructor_id, capacity) VALUES (?, ?, ?, ?)",
                (title, description, instructor_id, capacity))
        return Course(cursor.lastrowid, title, description, instructor_id, capacity, False)

    def get(self, course_id: int) -> Optional[Course]:
        with self._db.transaction() as conn:
            row = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
        return self._to_course(row) if row else None

    def set_published(self, course_id: int) -> None:
        with self._db.transaction() as conn:
            conn.execute("UPDATE courses SET published = 1 WHERE id = ?", (course_id,))

    def list_published(self) -> list:
        with self._db.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM courses WHERE published = 1 ORDER BY title COLLATE NOCASE, id").fetchall()
        return [self._to_course(r) for r in rows]

    def search_published(self, term: str) -> list:
        # Escape LIKE wildcards so a user typing % or _ matches those characters literally.
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        with self._db.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM courses WHERE published = 1 AND title LIKE ? ESCAPE '\\' "
                "ORDER BY title COLLATE NOCASE, id", (f"%{escaped}%",)).fetchall()
        return [self._to_course(r) for r in rows]

    @staticmethod
    def _to_course(row) -> Course:
        return Course(row["id"], row["title"], row["description"], row["instructor_id"],
                      row["capacity"], bool(row["published"]))


class CourseService:
    TITLE_MIN, TITLE_MAX, DESCRIPTION_MAX = 3, 100, 2000
    CAPACITY_MIN, CAPACITY_MAX, SEARCH_MAX = 1, 500, 100

    def __init__(self, repo: SqliteCourseRepository, audit: Optional[AuditLog] = None) -> None:
        self._repo = repo
        self._audit = audit or AuditLog()

    def create_course(self, actor: User, title: str, description: str, capacity: int) -> Course:
        require_role(actor, Role.INSTRUCTOR, Role.ADMIN)
        title = self._validate_title(title)
        self._validate_description(description)
        self._validate_capacity(capacity)
        course = self._repo.add(title, description, actor.id, capacity)
        self._audit.record("course_created", course_id=course.id, actor_id=actor.id)
        return course

    def publish_course(self, actor: User, course_id: int) -> Course:
        require_role(actor, Role.INSTRUCTOR, Role.ADMIN)
        course = self._repo.get(course_id)
        if course is None:
            raise NotFoundError("Course not found")
        if not self.can_manage(actor, course):
            raise AuthorizationError("Access denied")
        self._repo.set_published(course_id)
        self._audit.record("course_published", course_id=course_id, actor_id=actor.id)
        return self._repo.get(course_id)

    def get_course(self, actor: User, course_id: int) -> Course:
        """Drafts are invisible to everyone except their owner and administrators."""
        course = self._repo.get(course_id)
        if course is None or not (course.published or self.can_manage(actor, course)):
            raise NotFoundError("Course not found")
        return course

    def list_published(self) -> list:
        return self._repo.list_published()

    def search(self, term: str) -> list:
        if not isinstance(term, str) or len(term) > self.SEARCH_MAX:
            raise ValidationError("Invalid search term")
        return self._repo.search_published(term.strip())

    @staticmethod
    def can_manage(actor: User, course: Course) -> bool:
        return actor.role == Role.ADMIN or (actor.role == Role.INSTRUCTOR and course.instructor_id == actor.id)

    def _validate_title(self, title: object) -> str:
        if not isinstance(title, str) or not self.TITLE_MIN <= len(title.strip()) <= self.TITLE_MAX:
            raise ValidationError(f"Title must be {self.TITLE_MIN} to {self.TITLE_MAX} characters")
        return title.strip()

    def _validate_description(self, description: object) -> None:
        if not isinstance(description, str) or len(description) > self.DESCRIPTION_MAX:
            raise ValidationError(f"Description must be at most {self.DESCRIPTION_MAX} characters")

    def _validate_capacity(self, capacity: object) -> None:
        # bool is a subclass of int in Python, so it must be excluded explicitly.
        if (not isinstance(capacity, int) or isinstance(capacity, bool)
                or not self.CAPACITY_MIN <= capacity <= self.CAPACITY_MAX):
            raise ValidationError(f"Capacity must be a whole number from {self.CAPACITY_MIN} to {self.CAPACITY_MAX}")
