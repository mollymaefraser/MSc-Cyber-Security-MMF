"""The original, tightly coupled code from the brief (kept for comparison)."""


class EmailService:
    def send_email(self, user, message):
        print(f"Sending email to {user}: {message}")


class UserManager:
    def __init__(self):
        self.notifier = EmailService()  # Direct dependency

    def register_user(self, user):
        self.notifier.send_email(user, "Welcome!")
