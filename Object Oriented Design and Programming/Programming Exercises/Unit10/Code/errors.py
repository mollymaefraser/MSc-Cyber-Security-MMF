"""Exception hierarchy. Callers can catch ELearnError and never see internals."""


class ELearnError(Exception):
    pass


class ValidationError(ELearnError):
    pass


class DuplicateEmailError(ELearnError):
    pass


class AuthenticationError(ELearnError):
    pass


class AuthorizationError(ELearnError):
    pass


class TooManyAttemptsError(ELearnError):
    pass


class NotFoundError(ELearnError):
    pass


class CourseFullError(ELearnError):
    pass


class EnrolmentError(ELearnError):
    pass
