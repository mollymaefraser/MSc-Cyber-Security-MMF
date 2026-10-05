"""Presentation layer: translates calls into service operations and errors into status codes.

This stands in for HTTP handlers. It holds no business rules. It authenticates the caller,
validates the shape of raw input, delegates, and maps every failure to a safe response.
"""

from dataclasses import dataclass
from typing import Callable

from .errors import (AuthenticationError, AuthorizationError, CourseFullError, DuplicateEmailError,
                     EnrolmentError, NotFoundError, TooManyAttemptsError, ValidationError)


@dataclass(frozen=True)
class Response:
    status: int
    body: dict


_STATUS_FOR_ERROR = (
    (ValidationError, 400),
    (AuthenticationError, 401),
    (AuthorizationError, 403),
    (NotFoundError, 404),
    (DuplicateEmailError, 409),
    (CourseFullError, 409),
    (EnrolmentError, 409),
    (TooManyAttemptsError, 429),
)


def _course_dict(course) -> dict:
    return {"id": course.id, "title": course.title, "description": course.description,
            "capacity": course.capacity, "published": course.published}


class ApiController:
    def __init__(self, users, courses, enrolments) -> None:
        self._users = users
        self._courses = courses
        self._enrolments = enrolments

    # ---- accounts ----
    def register(self, email, password) -> Response:
        def action():
            user = self._users.register(email, password)
            return {"id": user.id, "email": user.email, "role": user.role.value}
        return self._run(action, 201)

    def login(self, email, password, client_id="unknown") -> Response:
        return self._run(lambda: {"token": self._users.authenticate(email, password, client_id)})

    def logout(self, token) -> Response:
        def action():
            self._users.logout(token)
            return {"message": "Logged out"}
        return self._run(action)

    def change_password(self, token, current_password, new_password) -> Response:
        def action():
            user = self._users.user_for_token(token)
            self._users.change_password(user.id, current_password, new_password)
            return {"message": "Password changed. Please log in again."}
        return self._run(action)

    # ---- courses ----
    def create_course(self, token, title, description, capacity) -> Response:
        def action():
            actor = self._users.user_for_token(token)
            return _course_dict(self._courses.create_course(actor, title, description, capacity))
        return self._run(action, 201)

    def publish_course(self, token, course_id) -> Response:
        def action():
            actor = self._users.user_for_token(token)
            return _course_dict(self._courses.publish_course(actor, self._int(course_id)))
        return self._run(action)

    def list_courses(self) -> Response:
        return self._run(lambda: {"courses": [_course_dict(c) for c in self._courses.list_published()]})

    def search_courses(self, term) -> Response:
        return self._run(lambda: {"courses": [_course_dict(c) for c in self._courses.search(term)]})

    # ---- enrolment ----
    def enrol(self, token, course_id) -> Response:
        def action():
            actor = self._users.user_for_token(token)
            enrolment = self._enrolments.enrol(actor, self._int(course_id))
            return {"course_id": enrolment.course_id, "student_id": enrolment.student_id}
        return self._run(action, 201)

    def unenrol(self, token, course_id) -> Response:
        def action():
            actor = self._users.user_for_token(token)
            self._enrolments.unenrol(actor, self._int(course_id))
            return {"message": "Unenrolled"}
        return self._run(action)

    def my_courses(self, token) -> Response:
        def action():
            actor = self._users.user_for_token(token)
            return {"courses": [_course_dict(c) for c in self._enrolments.courses_for_student(actor)]}
        return self._run(action)

    def roster(self, token, course_id) -> Response:
        def action():
            actor = self._users.user_for_token(token)
            return {"students": self._enrolments.roster(actor, self._int(course_id))}
        return self._run(action)

    # ---- helpers ----
    @staticmethod
    def _int(value) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError("Course id must be a whole number")
        return value

    @staticmethod
    def _run(action: Callable[[], dict], success_status: int = 200) -> Response:
        try:
            return Response(success_status, action())
        except Exception as exc:  # noqa: BLE001 - the last line of defence must catch everything
            for error_type, status in _STATUS_FOR_ERROR:
                if isinstance(exc, error_type):
                    detail = exc.args[0] if exc.args else "Request failed"
                    if isinstance(detail, list):
                        detail = "; ".join(detail)
                    return Response(status, {"error": str(detail)})
            return Response(500, {"error": "Internal server error"})  # details never leave the server
