"""Step 1 and 2: the abstraction (NotificationService) and its implementations."""

from abc import ABC, abstractmethod


class NotificationService(ABC):
    """The abstraction that high level code depends on."""

    @abstractmethod
    def send_notification(self, user, message):
        """Deliver a message to a user by whatever channel the implementation uses."""


class EmailService(NotificationService):
    def send_notification(self, user, message):
        print(f"Sending email to {user}: {message}")


class SMSService(NotificationService):
    def send_notification(self, user, message):
        print(f"Sending SMS to {user}: {message}")
