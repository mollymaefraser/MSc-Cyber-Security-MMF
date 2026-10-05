"""Composition root: the one place where concrete classes are chosen and wired together."""

from container import Container
from notifications import EmailService
from user_manager import UserManager


def manual_wiring():
    """Pure DI with no library: just pass the dependency in."""
    return UserManager(EmailService())


def container_wiring(channel="email"):
    container = Container()
    container.config.channel.from_value(channel)
    return container.user_manager()


if __name__ == "__main__":
    print("Manual wiring:")
    manual_wiring().register_user("molly@example.com")
    print("\nContainer, channel=email:")
    container_wiring("email").register_user("molly@example.com")
    print("\nContainer, channel=sms (no change to UserManager):")
    container_wiring("sms").register_user("+44 7700 900123")
