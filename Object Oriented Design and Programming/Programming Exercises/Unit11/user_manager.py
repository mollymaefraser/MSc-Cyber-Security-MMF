"""Step 3: UserManager receives its dependency instead of creating it."""

from notifications import NotificationService


class UserManager:
    def __init__(self, notifier: NotificationService):
        self._notifier = notifier  # injected through the constructor

    def register_user(self, user):
        self._notifier.send_notification(user, "Welcome!")
