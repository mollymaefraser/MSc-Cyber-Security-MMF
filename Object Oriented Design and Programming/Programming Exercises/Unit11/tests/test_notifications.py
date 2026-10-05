"""Tests for the concrete services on their own (the 'integration' side of the split).

These are kept separate from UserManager's unit tests. They exercise the real service.
Here the services only print, so the output is captured. A service that really called an
SMTP server or an SMS gateway would be tested against a local test server or a sandbox account.
"""

import io
import unittest
from contextlib import redirect_stdout

from notifications import EmailService, NotificationService, SMSService


def capture(service, user, message):
    out = io.StringIO()
    with redirect_stdout(out):
        service.send_notification(user, message)
    return out.getvalue()


class EmailServiceTests(unittest.TestCase):
    def test_is_a_notification_service(self):
        self.assertIsInstance(EmailService(), NotificationService)

    def test_formats_the_email(self):
        self.assertEqual(capture(EmailService(), "molly@example.com", "Welcome!"),
                         "Sending email to molly@example.com: Welcome!\n")


class SMSServiceTests(unittest.TestCase):
    def test_is_a_notification_service(self):
        self.assertIsInstance(SMSService(), NotificationService)

    def test_formats_the_sms(self):
        self.assertEqual(capture(SMSService(), "+44 7700 900123", "Welcome!"),
                         "Sending SMS to +44 7700 900123: Welcome!\n")


if __name__ == "__main__":
    unittest.main()
