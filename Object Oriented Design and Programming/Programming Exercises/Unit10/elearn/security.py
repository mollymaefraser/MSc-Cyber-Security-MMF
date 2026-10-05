"""Authorisation helper shared by every module."""

from .errors import AuthorizationError


def require_role(user, *roles) -> None:
    """Deny by default. The message deliberately does not say which roles would be accepted."""
    if user.role not in roles:
        raise AuthorizationError("Access denied")
