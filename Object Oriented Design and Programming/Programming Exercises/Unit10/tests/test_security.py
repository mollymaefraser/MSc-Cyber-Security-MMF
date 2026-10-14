import unittest

from elearn.errors import AuthorisationError
from elearn.security import require_role
from elearn.users import Role, User


def user_with(role):
    return User(1, "x@example.com", role, 0.0)


class RequireRoleTests(unittest.TestCase):
    def test_allowed_role_passes(self):
        require_role(user_with(Role.INSTRUCTOR), Role.INSTRUCTOR, Role.ADMIN)

    def test_other_role_is_denied(self):
        with self.assertRaises(AuthorisationError):
            require_role(user_with(Role.STUDENT), Role.INSTRUCTOR, Role.ADMIN)

    def test_denial_message_does_not_reveal_which_roles_would_work(self):
        with self.assertRaises(AuthorisationError) as ctx:
            require_role(user_with(Role.STUDENT), Role.ADMIN)
        self.assertNotIn("admin", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
