"""Unit tests for UserManager in isolation. No email is ever sent."""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, create_autospec

from notifications import EmailService, NotificationService, SMSService
from user_manager import UserManager


class RecordingNotifier(NotificationService):
    """A hand written test double (a fake) that records what it was asked to send."""

    def __init__(self):
        self.sent = []

    def send_notification(self, user, message):
        self.sent.append((user, message))


class UserManagerWithMock(unittest.TestCase):
    def test_register_user_sends_a_welcome_message(self):
        notifier = Mock(spec=NotificationService)
        UserManager(notifier).register_user("student@example.com")
        notifier.send_notification.assert_called_once_with("student@example.com", "Welcome!")

    def test_nothing_real_is_sent_when_a_mock_is_injected(self):
        out = io.StringIO()
        with redirect_stdout(out):
            UserManager(Mock(spec=NotificationService)).register_user("student@example.com")
        self.assertEqual(out.getvalue(), "")

    def test_each_registration_sends_exactly_one_message_to_that_user(self):
        notifier = Mock(spec=NotificationService)
        manager = UserManager(notifier)
        manager.register_user("a@example.com")
        manager.register_user("b@example.com")
        self.assertEqual(notifier.send_notification.call_count, 2)
        self.assertEqual([c.args[0] for c in notifier.send_notification.call_args_list],
                         ["a@example.com", "b@example.com"])

    def test_mock_with_spec_rejects_methods_the_interface_does_not_have(self):
        notifier = Mock(spec=NotificationService)
        with self.assertRaises(AttributeError):
            notifier.send_email("x", "y")  # the old, email specific method name

    def test_autospec_also_checks_the_call_signature(self):
        notifier = create_autospec(NotificationService, instance=True)
        with self.assertRaises(TypeError):
            notifier.send_notification("only one argument")


class UserManagerWithFake(unittest.TestCase):
    def test_a_hand_written_fake_records_the_message(self):
        notifier = RecordingNotifier()
        UserManager(notifier).register_user("student@example.com")
        self.assertEqual(notifier.sent, [("student@example.com", "Welcome!")])


class UserManagerBehaviour(unittest.TestCase):
    def test_a_failing_notifier_propagates_its_error_to_the_caller(self):
        notifier = Mock(spec=NotificationService)
        notifier.send_notification.side_effect = ConnectionError("SMTP server down")
        with self.assertRaises(ConnectionError):
            UserManager(notifier).register_user("student@example.com")

    def test_the_dependency_is_required(self):
        with self.assertRaises(TypeError):
            UserManager()

    def test_the_abstract_interface_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            NotificationService()

    def test_any_notification_service_can_be_substituted(self):
        for service in (EmailService(), SMSService(), RecordingNotifier()):
            out = io.StringIO()
            with redirect_stdout(out):
                UserManager(service).register_user("student@example.com")  # must not raise


if __name__ == "__main__":
    unittest.main()
