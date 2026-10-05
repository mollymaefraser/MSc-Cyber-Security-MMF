# Refactoring to Dependency Injection and Inversion of Control

## 1. Overview

The original UserManager creates its own EmailService, which couples it to one notification channel and makes it impossible to unit test without triggering the real send. This document refactors it using Dependency Injection (DI) and Inversion of Control (IoC), shows how the refactor makes the class testable in isolation, and then goes further with a DI container and a second notification channel (SMS).

Everything below was run, not just written. The refactored design has 24 passing tests, and I also checked that those tests fail if the old tight coupling is put back.

---

## 2. Problems with the Initial Code

```python
"""The original, tightly coupled code from the brief (kept for comparison)."""


class EmailService:
    def send_email(self, user, message):
        print(f"Sending email to {user}: {message}")


class UserManager:
    def __init__(self):
        self.notifier = EmailService()  # Direct dependency

    def register_user(self, user):
        self.notifier.send_email(user, "Welcome!")
```

Tight coupling. UserManager decides which concrete class to use, inside its own constructor. Switching to SMS or push notifications means editing UserManager, which breaks the Open/Closed Principle. It also breaks the Dependency Inversion Principle, because a high level policy class (register a user) depends directly on a low level detail (how an email is sent).

Low testability. Constructing a UserManager always creates a real EmailService, so a test cannot avoid the real send. The only workaround is patching a class name inside another module, which works but is fragile, because the test is now tied to an internal implementation detail. The tests in tests/test_original.py demonstrate all three points:

```
$ python3 -m unittest tests.test_original -v
test_a_test_cannot_avoid_the_real_send_without_patching_module_internals (OriginalCodeProblems) ... ok
test_constructing_the_manager_always_creates_a_real_email_service (OriginalCodeProblems) ... ok
test_the_only_workaround_is_patching_a_hard_coded_global (OriginalCodeProblems) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.001s

OK
```

A third, subtler problem is vocabulary. The method is called send_email, so even if a second service were added, the name of the interface would still say email.

---

## 3. Key Ideas

Dependency Injection means an object receives the collaborators it needs from outside, usually through its constructor, instead of creating them itself.

Inversion of Control means the responsibility for creating and wiring objects moves out of the business classes into a separate place, called the composition root (or into a container). UserManager no longer controls which notifier it gets. The code that assembles the application does.

Dependency Inversion (the D in SOLID) is the design principle that makes this work: both UserManager and the concrete services depend on an abstraction, NotificationService, so the dependency arrows point toward the interface and not toward a detail.

---

## 4. Refactoring Steps

### Step 1: Introduce an interface (NotificationService)

The interface uses a channel neutral method name, send_notification, rather than send_email.

### Step 2: Implement the interface (EmailService), and add SMSService

```python
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
```

EmailService changes only in name and base class. SMSService is a new class that required no change to any existing code, which is the Open/Closed Principle in action.

### Step 3: Modify UserManager to accept its dependency

```python
"""Step 3: UserManager receives its dependency instead of creating it."""

from notifications import NotificationService


class UserManager:
    def __init__(self, notifier: NotificationService):
        self._notifier = notifier  # injected through the constructor

    def register_user(self, user):
        self._notifier.send_notification(user, "Welcome!")
```

The constructor now takes a NotificationService. UserManager does not know or care whether it holds an email service, an SMS service, a test double or something written next year. Any implementation can be substituted without breaking UserManager, which is the Liskov Substitution Principle.

### Wiring it together (the composition root)

```python
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
```

The manual version is already full dependency injection. No library is needed. The composition root is the only place that names concrete classes.

Real output of the demo:

```
$ python3 main.py
Manual wiring:
Sending email to molly@example.com: Welcome!

Container, channel=email:
Sending email to molly@example.com: Welcome!

Container, channel=sms (no change to UserManager):
Sending SMS to +44 7700 900123: Welcome!
```

---

## 5. Unit Tests Demonstrating the Benefits of DI

The scenario: verify that UserManager sends a welcome message without sending a real email.

1. Create a mock notification service.
2. Test UserManager in isolation by injecting it.

```python
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
        UserManager(notifier).register_user("molly@example.com")
        notifier.send_notification.assert_called_once_with("molly@example.com", "Welcome!")

    def test_nothing_real_is_sent_when_a_mock_is_injected(self):
        out = io.StringIO()
        with redirect_stdout(out):
            UserManager(Mock(spec=NotificationService)).register_user("molly@example.com")
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
        UserManager(notifier).register_user("molly@example.com")
        self.assertEqual(notifier.sent, [("molly@example.com", "Welcome!")])


class UserManagerBehaviour(unittest.TestCase):
    def test_a_failing_notifier_propagates_its_error_to_the_caller(self):
        notifier = Mock(spec=NotificationService)
        notifier.send_notification.side_effect = ConnectionError("SMTP server down")
        with self.assertRaises(ConnectionError):
            UserManager(notifier).register_user("molly@example.com")

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
                UserManager(service).register_user("molly@example.com")  # must not raise


if __name__ == "__main__":
    unittest.main()
```

What each group of tests demonstrates:

The mock tests. The mock is created with spec=NotificationService, so it only allows calls that exist on the real interface. That matters, because an unspecced Mock accepts any method name, so a test could pass even if UserManager called a method that does not exist. One test proves the spec works by showing that the old name, send_email, now raises an AttributeError. create_autospec goes one step further and also checks the call signature.

The fake. RecordingNotifier is a small hand written test double that stores what it was asked to send. A mock is quicker to set up and is best for checking that a particular call happened. A fake reads like ordinary code and can be clearer when a test only needs a believable collaborator. Neither is always better, and I included both so the trade-off is visible.

Behaviour at the edges. A failing notifier propagates its error to the caller, which makes the behaviour explicit (and a design decision worth revisiting, since failing to send a welcome message probably should not stop a registration succeeding in a real system). The dependency is required, the abstract interface cannot be instantiated, and every implementation can be substituted.

---

## 6. Further Improvements

### 6.1 A DI container (dependency-injector)

A container automates the wiring. Instead of constructing objects by hand in main, you declare how each one is built and the container assembles them.

```python
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
```

The Selector provider chooses the implementation from configuration, so switching from email to SMS is a settings change with no code edit. Providers also control lifetime: Singleton creates one shared instance, and Factory creates a new one each time.

The container also helps testing. A provider can be overridden with a mock, for the duration of a with block, without touching any production code:

```python
with container.notification_service.override(providers.Object(mock_notifier)):
    container.user_manager().register_user("molly@example.com")
```

### 6.2 More services

SMSService (shown in Step 2) plugs in through the same interface. A push notification service would be the same again. Further extensions that follow naturally from the design are a composite notifier that sends through several channels at once, and a logging or retry decorator that wraps any notifier.

### 6.3 Testing the real services separately

UserManager's tests prove how UserManager behaves. They say nothing about whether EmailService really sends an email, so the concrete services get their own tests, kept separate:

```python
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
```

In this exercise the services only print, so the tests capture standard output. A service that really called an SMTP server or an SMS gateway would be tested against a local test server or a vendor sandbox account, run less often than the fast unit tests, and marked separately in the test suite.

---

## 7. Test Results

```
$ python3 -m unittest discover -s tests -t . -v
test_container_can_be_overridden_with_a_mock_in_tests (ContainerWiring) ... ok
test_email_channel_wires_an_email_service (ContainerWiring) ... ok
test_factory_provider_creates_a_new_manager_each_time (ContainerWiring) ... ok
test_override_is_undone_after_the_with_block (ContainerWiring) ... ok
test_singleton_providers_share_one_instance (ContainerWiring) ... ok
test_sms_channel_wires_an_sms_service_without_changing_user_manager (ContainerWiring) ... ok
test_unknown_channel_fails_loudly (ContainerWiring) ... ok
test_formats_the_email (EmailServiceTests) ... ok
test_is_a_notification_service (EmailServiceTests) ... ok
test_formats_the_sms (SMSServiceTests) ... ok
test_is_a_notification_service (SMSServiceTests) ... ok
test_a_test_cannot_avoid_the_real_send_without_patching_module_internals (OriginalCodeProblems) ... ok
test_constructing_the_manager_always_creates_a_real_email_service (OriginalCodeProblems) ... ok
test_the_only_workaround_is_patching_a_hard_coded_global (OriginalCodeProblems) ... ok
test_a_failing_notifier_propagates_its_error_to_the_caller (UserManagerBehaviour) ... ok
test_any_notification_service_can_be_substituted (UserManagerBehaviour) ... ok
test_the_abstract_interface_cannot_be_instantiated (UserManagerBehaviour) ... ok
test_the_dependency_is_required (UserManagerBehaviour) ... ok
test_a_hand_written_fake_records_the_message (UserManagerWithFake) ... ok
test_autospec_also_checks_the_call_signature (UserManagerWithMock) ... ok
test_each_registration_sends_exactly_one_message_to_that_user (UserManagerWithMock) ... ok
test_mock_with_spec_rejects_methods_the_interface_does_not_have (UserManagerWithMock) ... ok
test_nothing_real_is_sent_when_a_mock_is_injected (UserManagerWithMock) ... ok
test_register_user_sends_a_welcome_message (UserManagerWithMock) ... ok

----------------------------------------------------------------------
Ran 24 tests in 0.010s

OK
```

Do the tests actually protect the design? To check, I temporarily changed UserManager so it ignored the injected dependency and created its own EmailService again, which is exactly the original flaw. Eight tests failed, so the suite does detect a regression to tight coupling. I then restored the file and all 24 passed again.

---

## 8. SOLID Principles Applied

| Principle | How the refactor applies it |
|---|---|
| Single Responsibility | UserManager registers users. It no longer also decides how notifications are delivered or created |
| Open/Closed | New channels (SMS, push) are added as new classes with no edit to UserManager |
| Liskov Substitution | Any NotificationService can replace another, and a test checks every implementation in turn |
| Interface Segregation | NotificationService has one small method that UserManager actually uses |
| Dependency Inversion | UserManager depends on the abstraction, and the composition root supplies the detail |

---

## 9. Trade-offs and Cautions

More moving parts. For a class this small, an interface plus a container is more machinery than the problem needs. The refactor pays off when there are, or will be, several implementations or real tests to write. The manual constructor injection in main is often enough, and a container becomes worthwhile when the object graph grows.

Container magic. Containers can make it harder to see where an object came from. Keep the container at the edge of the application (the composition root) and let the business classes stay ordinary classes that just take their arguments. Passing the container itself into business classes, so they ask it for what they need, is the Service Locator anti-pattern and hides dependencies again.

Constructor injection is preferred here because the dependency is mandatory and the object is never half built. Setter injection allows optional dependencies but lets an object exist in an unusable state.

Mocks can mislead. A mock that does not match the real interface can pass while production fails, which is why the tests use spec and autospec, and why the real services are tested separately.

Hard coded message. "Welcome!" is still fixed inside UserManager. If different messages or languages are needed, the message (or a message builder) would be another dependency to inject.

---

## 10. Files

- original.py: the tightly coupled code from the brief
- notifications.py: NotificationService, EmailService, SMSService
- user_manager.py: the refactored UserManager
- container.py: the dependency-injector container
- main.py: composition root and demo
- tests/test_original.py, test_user_manager.py, test_notifications.py, test_container.py

Developed and tested on Python 3.11. The container alone needs the dependency-injector package (pip install dependency-injector). Run the tests with python3 -m unittest discover -s tests -t . -v
