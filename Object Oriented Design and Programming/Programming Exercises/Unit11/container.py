"""Further improvement 1: a DI container (dependency-injector) that wires everything."""

from dependency_injector import containers, providers

from notifications import EmailService, SMSService
from user_manager import UserManager


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    email_service = providers.Singleton(EmailService)
    sms_service = providers.Singleton(SMSService)

    # Chooses the implementation from configuration, so switching channel is a settings change.
    notification_service = providers.Selector(
        config.channel,
        email=email_service,
        sms=sms_service,
    )

    user_manager = providers.Factory(UserManager, notifier=notification_service)
