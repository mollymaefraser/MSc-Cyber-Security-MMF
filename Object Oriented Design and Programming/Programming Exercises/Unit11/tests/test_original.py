"""Shows why the original design is hard to test."""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from original import UserManager


class OriginalCodeProblems(unittest.TestCase):
    def test_constructing_the_manager_always_creates_a_real_email_service(self):
        manager = UserManager()
        self.assertEqual(type(manager.notifier).__name__, "EmailService")

    def test_a_test_cannot_avoid_the_real_send_without_patching_module_internals(self):
        out = io.StringIO()
        with redirect_stdout(out):
            UserManager().register_user("molly@example.com")
        # The real "email" was sent during the test. The only evidence is captured console output.
        self.assertIn("Sending email to molly@example.com", out.getvalue())

    def test_the_only_workaround_is_patching_a_hard_coded_global(self):
        with patch("original.EmailService") as fake_cls:
            UserManager().register_user("molly@example.com")
        fake_cls.return_value.send_email.assert_called_once_with("molly@example.com", "Welcome!")
        # This works, but it depends on the name of a class inside another module,
        # and it still cannot switch the manager to SMS.


if __name__ == "__main__":
    unittest.main()
