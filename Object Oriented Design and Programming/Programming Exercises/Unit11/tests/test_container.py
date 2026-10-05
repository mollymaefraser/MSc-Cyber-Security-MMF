"""Tests for the DI container wiring."""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock

from dependency_injector import providers

from container import Container
from notifications import EmailService, NotificationService, SMSService
from user_manager import UserManager


def build(channel):
    container = Container()
    container.config.channel.from_value(channel)
    return container


class ContainerWiring(unittest.TestCase):
    def test_email_channel_wires_an_email_service(self):
        manager = build("email").user_manager()
        self.assertIsInstance(manager, UserManager)
        self.assertIsInstance(manager._notifier, EmailService)

    def test_sms_channel_wires_an_sms_service_without_changing_user_manager(self):
        self.assertIsInstance(build("sms").user_manager()._notifier, SMSService)

    def test_singleton_providers_share_one_instance(self):
        container = build("email")
        self.assertIs(container.user_manager()._notifier, container.user_manager()._notifier)

    def test_factory_provider_creates_a_new_manager_each_time(self):
        container = build("email")
        self.assertIsNot(container.user_manager(), container.user_manager())

    def test_unknown_channel_fails_loudly(self):
        with self.assertRaises(Exception):
            build("carrier-pigeon").user_manager()

    def test_container_can_be_overridden_with_a_mock_in_tests(self):
        container = build("email")
        mock_notifier = Mock(spec=NotificationService)
        with container.notification_service.override(providers.Object(mock_notifier)):
            container.user_manager().register_user("molly@example.com")
        mock_notifier.send_notification.assert_called_once_with("molly@example.com", "Welcome!")

    def test_override_is_undone_after_the_with_block(self):
        container = build("email")
        with container.notification_service.override(providers.Object(Mock(spec=NotificationService))):
            pass
        self.assertIsInstance(container.user_manager()._notifier, EmailService)


if __name__ == "__main__":
    unittest.main()
