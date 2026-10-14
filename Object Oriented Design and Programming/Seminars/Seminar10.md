# Unit 10 Seminar

## Title: Test-Driven Development (TDD) and Unit Testing

---

## Learning Outcomes

By the end of this seminar, students should be able to:

- Explain the TDD cycle and its benefits for software development.
- Write meaningful and isolated unit tests to verify the behaviour of individual components.
- Use TDD to develop a software component, following the cycle of writing tests, implementing code and refactoring.
- Use TDD and unit testing to address real world software development challenges.

---

## General Overview

This seminar introduces Test Driven Development (TDD), a software development approach where tests are written before the code they test. Students will see why unit testing matters for code quality, bug reduction and long term maintainability, and will work through a practical exercise that uses TDD to build a signup risk checking component from nothing.

The same exercise is then extended in three further stages: refactoring the finished component with advanced design patterns, isolating it from external dependencies using mocking frameworks, and using AI assisted tools to help generate and review test cases, with every generated test reviewed by a person before it is kept.

---

## Part 1: Introduction to Test Driven Development

### The TDD Cycle

TDD follows a short, repeating cycle, often called red, green, refactor:

1. Write a failing test. Decide what the code should do before writing any of it, and write a test that describes that behaviour. It fails, since the code does not exist yet, which is expected and checked for.
2. Write the minimum code to pass the test. Implement only enough to make the test pass, resisting the urge to add anything the current test does not actually require.
3. Refactor the code. With a passing test in place as a safety net, improve the internal structure, naming or duplication of the code, then run the test again to confirm nothing broke.

### Benefits of TDD

- Improved code quality, since every piece of behaviour has a test that defines it before it is written.
- Better design, since writing the test first forces a component's interface to be considered before its implementation, which tends to produce smaller, more focused classes.
- Reduced debugging time, since a failing test usually points directly at the change that broke it, rather than leaving the fault to be found by manual inspection later.
- A safety net for change, since an existing suite of tests can be rerun after any later edit to confirm old behaviour still holds.

---

## Part 2: The Importance of Unit Testing

A unit test checks one small, isolated piece of behaviour, typically a single method or function, independently of the rest of the system. Unit testing contributes to a project in three main ways:

- Ensuring correctness by verifying each component behaves as intended on its own, before it is combined with anything else.
- Reducing bugs by catching mistakes at the point they are introduced, rather than later when several components are interacting and a fault is harder to trace back to its source.
- Facilitating maintainability by giving future changes, including refactoring, a safety net: a change that breaks existing behaviour is caught immediately rather than discovered in production.

### Best Practices for Writing Effective Unit Tests

- Test isolation: a unit test should not depend on another test's state, external services, the real clock, or the order tests happen to run in.
- Meaningful test names: a test name should describe the behaviour being checked, for example test_rejects_known_common_password, so a failure is understandable from its name alone.
- One logical assertion per test where practical, so a failure points at exactly one thing that went wrong.
- Fast tests: a suite that takes minutes to run gets run less often. Mocking slow or external dependencies, covered in Part 5, is one of the main ways this is achieved.

---

## Part 3: Practical Exercise, Building a Component with TDD

The exercise builds a signup risk checker for a fictional service: before an account is created, its password is validated and the signup attempt is scored for fraud risk.

### Working through the cycle

The first slice of behaviour was a minimum password length rule, built in the usual order:

1. Red: a test was written first, asserting that a six character password is rejected.
2. Green: a MinimumLengthStrategy class was written with just enough logic to satisfy that one test, an if statement comparing the password's length against a minimum.
3. Refactor: once a second test for an acceptable password also passed, the check method's wording was tidied so the returned message reads clearly, and the hardcoded minimum of ten was pulled out into a constructor parameter so the same class could be reused with a different minimum later.

The same cycle was then repeated for each further rule in turn: a complexity rule requiring both a letter and a digit, and a check against a short list of known common passwords. Each rule's test was written before its class existed, each class was written to satisfy only its own test, and the suite was rerun after every step to confirm nothing earlier had broken.

Once three independent rules existed, a PasswordValidator class was introduced to run a configurable list of them together and collect every violation, rather than stopping at the first failure. This is a refactoring step in its own right: no new behaviour was added, but the three rules became easier to combine and extend. The full set of these tests, and the resulting classes, are in Appendix A and Appendix B.

This same pattern, a short cycle repeated once per small piece of behaviour, is how the rest of the component was grown: a basic SignupService combining the validator with a password hasher and a fraud scoring check was added once the validator itself was solid, again one test at a time.

---

## Part 4: Advanced Design Patterns Applied to the Same Exercise

Once the core component worked and was covered by tests, it was refactored using four further patterns, without changing what it does from the outside. Every test written in Part 3 still passes after each of these changes, which is what the tests are there to confirm.

### Strategy: interchangeable password validation rules

MinimumLengthStrategy, ComplexityStrategy and CommonPasswordStrategy all implement the same PasswordValidationStrategy interface. PasswordValidator holds a list of them and does not know or care which concrete rules it has been given. Adding a new rule, for example checking a password against a breached password list, means writing one new class, with no change to PasswordValidator or to any of the existing rule classes.

### Decorator: adding logging and rate limiting without touching the core service

LoggingSignupDecorator and RateLimitingSignupDecorator both wrap a SignupServiceComponent and add behaviour before or after calling through to the wrapped object. SignupService itself has no logging code and no rate limiting code anywhere inside it. The two concerns are layered on from outside, and can be combined in either order, or left off entirely for a test that wants the plain service, which is what most of the tests in Appendix D do.

### Visitor: separating reporting and analytics from the result itself

SignupResult is a plain data holder. ComplianceReportVisitor and AnalyticsVisitor each implement SignupResultVisitor and do entirely different things with the same stream of results, one collecting high risk signups for a compliance team, the other computing overall volume and average risk. Neither visitor needs to know about the other, and a third kind of report can be added later as a third visitor class, without editing SignupResult or either existing visitor.

### Abstract Factory: families of related objects per auth provider

StandardAuthProviderFactory and EnterpriseAuthProviderFactory each produce a matched validator and hasher. The enterprise factory's validator enforces a longer minimum password length, reflecting a stricter policy for enterprise customers, while both factories still produce objects that satisfy the same two interfaces. Code using a factory never needs to know which concrete factory it was given, only that it will receive a working validator and hasher together.

### AI oriented patterns: Model Registry and Feature Store

Two further abstractions model how an AI component would typically sit inside a larger system, kept here as deliberately simple mock implementations.

ModelRegistry manages named, versioned models. A caller can ask for the latest version of a model or a specific named version, without knowing how models are stored or trained. In this exercise it holds a single rule based stand in for a fraud scoring model, SimpleRuleFraudModel, registered under the name fraud_risk.

FeatureStore centralises how a signup attempt's features, such as how many recent signups have come from the same IP address, are computed, so that every caller reads those features the same way rather than each writing its own version of that logic. FraudScoringService depends on both abstractions, and is the one place in the system that actually calls a model with a set of features.

Both are deliberately simple. They matter here because they give the rest of the codebase a stable interface to depend on, so a real model registry or feature store, or an entirely different fraud detection approach, could be substituted later without any other class needing to change.

---

## Part 5: Mocking Frameworks

### Why the fraud scoring dependency needs to be isolated

SignupService depends on FraudScoringService, which in a real system would eventually call out to an actual model, a database, or both. A unit test for SignupService should not need a real model or a real database to run, both because that would make the test slow, and because a fault in the fraud scoring logic should show up as a failure in a test for FraudScoringService itself, not as a confusing failure somewhere inside SignupService's tests too.

### Dependency injection is what makes this possible

SignupService receives its FraudScoringService collaborator through its constructor, rather than constructing one itself internally. This is dependency injection, and it is the reason a test can hand SignupService a mock or a stub instead of the real thing, with no change needed to SignupService itself.

### Mocks, with unittest.mock

```python
fraud_service = Mock(spec=FraudScoringService)
fraud_service.score.return_value = 0.1
fraud_service.is_high_risk.return_value = False

service = SignupService(validator, hasher, fraud_service)
result = service.signup("person@example.com", "correcthorse9", "10.0.0.1")

fraud_service.score.assert_called_once_with("person@example.com", "10.0.0.1")
```

The spec=FraudScoringService argument validates the interface contract: the mock only allows calls to methods that actually exist on the real class, so a typo in a method name fails the test immediately instead of silently creating a new attribute, as a plain Mock() with no spec would do. create_autospec goes one step further and also checks that calls match the real method's signature, which is demonstrated in Appendix D.

### Stubs, as a hand written alternative

```python
class StubFraudScoringService:
    def score(self, email, ip):
        return 0.05
    def is_high_risk(self, score):
        return score >= 0.5
```

A stub is a small, real class that returns fixed, realistic answers, rather than a dynamically generated object with configured return values. Both are test doubles. A mock is usually quicker to set up and is well suited to checking that a particular call happened with particular arguments, as in assert_called_once_with above. A stub reads like ordinary code and can be a clearer choice when a test mainly needs a believable collaborator to exist, rather than needing to verify exactly how it was called. Which one to reach for is a judgement call, not a fixed rule, and Appendix D includes a working example of each.

### Validating behaviour and contracts together

The tests in Appendix D check two different things side by side: that SignupService behaves correctly given a particular fraud score, which is ordinary behavioural testing, and that the mock used to provide that score actually matches the real FraudScoringService interface, which is what spec and create_autospec are for. Testing behaviour without also checking the contract risks a suite that passes happily against a mock that no longer resembles the real dependency it stands in for.

---

## Part 6: AI Driven Testing

AI assisted tools can help with testing in a few concrete ways: suggesting test cases for behaviour that has not yet been covered, proposing edge cases a developer might not think to try, and flagging code paths that look under tested for regression purposes.

Three such suggestions were used in Appendix E of this exercise: a very long password, a password containing non ASCII characters, and an empty IP address string being checked against the rate limiter. Each was reviewed before being added. A further suggestion, fuzzing the password argument with random byte sequences, was considered and not added, since SignupService only ever receives a Python string from the form layer in this system, so that scenario cannot actually occur here and testing it would not check anything real.

An AI suggested test case still has to be checked before it goes in. Three things remain the developer's responsibility, whatever tool proposed the test:

- Human verification, confirming the suggested scenario can actually happen and is worth covering, before it is added to the suite.
- Test quality, making sure an added test asserts something meaningful rather than simply running code without checking its result.
- Engineering judgement, deciding which suggestions are worth keeping and which would only add noise to the suite, as with the discarded fourth suggestion above.

---

## Seminar Preparation

### 1. Review the Following Topics
- Test Driven Development: the TDD cycle and its benefits.
- Unit Testing: best practices for writing effective unit tests.

### 2. Set Up Your Development Environment
- Ensure you have a working Python or Java development environment.
- Install necessary testing frameworks (for example, unittest or pytest for Python, JUnit for Java).

### 3. Prepare Questions
- Come prepared with questions or topics you find challenging, for example how to write meaningful test cases, or how to handle complex dependencies in unit tests.

### 4. Practice Basic Testing Concepts
- Write simple unit tests for basic functions, for example a function that adds two numbers.

---

## Checklist Before Seminar

- [ ] Reviewed the TDD cycle (red, green, refactor) and its benefits
- [ ] Reviewed unit testing best practices, including test isolation and meaningful naming
- [ ] Python (or Java) environment installed, with a testing framework available
- [ ] Prepared at least one question on a challenging topic
- [ ] Practised writing a basic unit test for a simple function

---

## Appendix A: Password Validation Strategies, Validator and Hasher

```python
import re
from abc import ABC, abstractmethod
from typing import Optional


class ValidationError(Exception):
    def __init__(self, violations: list):
        self.violations = violations
        super().__init__("; ".join(violations))


class PasswordValidationStrategy(ABC):
    @abstractmethod
    def check(self, password: str) -> Optional[str]:
        """Return a violation message, or None if the password passes this rule."""


class MinimumLengthStrategy(PasswordValidationStrategy):
    def __init__(self, minimum: int = 10) -> None:
        self._minimum = minimum

    def check(self, password: str) -> Optional[str]:
        if len(password) < self._minimum:
            return f"Password must be at least {self._minimum} characters long"
        return None


class ComplexityStrategy(PasswordValidationStrategy):
    def check(self, password: str) -> Optional[str]:
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            return "Password must contain at least one letter and one digit"
        return None


class CommonPasswordStrategy(PasswordValidationStrategy):
    _BLOCKED = {"password123", "admin123", "letmein123"}

    def check(self, password: str) -> Optional[str]:
        if password.lower() in self._BLOCKED:
            return "That password is too common to be used"
        return None


class PasswordValidator:
    def __init__(self, strategies: list) -> None:
        self._strategies = strategies

    def validate(self, password: str) -> None:
        violations = [v for v in (s.check(password) for s in self._strategies) if v]
        if violations:
            raise ValidationError(violations)


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str: ...


class SimpleHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return f"hashed:{len(password)}:{hash(password)}"
```

## Appendix B: Tests Written During the TDD Cycle

```python
import unittest
from signup_system import (
    CommonPasswordStrategy, ComplexityStrategy, MinimumLengthStrategy,
    PasswordValidator, ValidationError,
)


class MinimumLengthStrategyTests(unittest.TestCase):
    def test_rejects_password_shorter_than_minimum(self):
        strategy = MinimumLengthStrategy(minimum=10)
        self.assertIsNotNone(strategy.check("short1"))

    def test_accepts_password_at_minimum_length(self):
        strategy = MinimumLengthStrategy(minimum=10)
        self.assertIsNone(strategy.check("1234567890"))


class ComplexityStrategyTests(unittest.TestCase):
    def test_rejects_password_with_no_digit(self):
        self.assertIsNotNone(ComplexityStrategy().check("onlyletters"))

    def test_rejects_password_with_no_letter(self):
        self.assertIsNotNone(ComplexityStrategy().check("12345678"))

    def test_accepts_password_with_letter_and_digit(self):
        self.assertIsNone(ComplexityStrategy().check("letters123"))


class CommonPasswordStrategyTests(unittest.TestCase):
    def test_rejects_known_common_password(self):
        self.assertIsNotNone(CommonPasswordStrategy().check("password123"))

    def test_accepts_uncommon_password(self):
        self.assertIsNone(CommonPasswordStrategy().check("correcthorsebattery9"))


class PasswordValidatorTests(unittest.TestCase):
    def test_passes_when_every_strategy_passes(self):
        validator = PasswordValidator([MinimumLengthStrategy(10), ComplexityStrategy()])
        validator.validate("correcthorse9")  # must not raise

    def test_collects_every_violation_not_just_the_first(self):
        validator = PasswordValidator([MinimumLengthStrategy(10), ComplexityStrategy()])
        with self.assertRaises(ValidationError) as ctx:
            validator.validate("abc")
        self.assertEqual(len(ctx.exception.violations), 2)
```

## Appendix C: Abstract Factory, Model Registry, Feature Store, Core Service and Decorators

```python
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional


class RateLimitedError(Exception):
    pass


@dataclass(frozen=True)
class SignupResult:
    email: str
    accepted: bool
    risk_score: float
    flagged_as_high_risk: bool

    def accept(self, visitor: "SignupResultVisitor") -> None:
        visitor.visit_signup_result(self)


# Abstract Factory
class AuthProviderFactory(ABC):
    @abstractmethod
    def create_validator(self) -> "PasswordValidator": ...

    @abstractmethod
    def create_hasher(self) -> "PasswordHasher": ...


class StandardAuthProviderFactory(AuthProviderFactory):
    def create_validator(self):
        return PasswordValidator([
            MinimumLengthStrategy(minimum=10),
            ComplexityStrategy(),
            CommonPasswordStrategy(),
        ])

    def create_hasher(self):
        return SimpleHasher()


class EnterpriseAuthProviderFactory(AuthProviderFactory):
    def create_validator(self):
        return PasswordValidator([
            MinimumLengthStrategy(minimum=14),
            ComplexityStrategy(),
            CommonPasswordStrategy(),
        ])

    def create_hasher(self):
        return SimpleHasher()


# AI oriented abstractions
class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict = {}

    def register(self, name: str, version: str, model: Callable) -> None:
        self._models.setdefault(name, {})[version] = model

    def get(self, name: str, version: Optional[str] = None) -> Callable:
        versions = self._models.get(name)
        if not versions:
            raise KeyError(f"No model registered under '{name}'")
        if version is None:
            latest = sorted(versions.keys())[-1]
            return versions[latest]
        try:
            return versions[version]
        except KeyError:
            raise KeyError(f"Model '{name}' has no version '{version}'") from None


class FeatureStore:
    def __init__(self) -> None:
        self._recent_signups_by_ip: dict = {}

    def record_signup(self, ip: str) -> None:
        self._recent_signups_by_ip[ip] = self._recent_signups_by_ip.get(ip, 0) + 1

    def get_features(self, ip: str, email: str) -> dict:
        return {
            "recent_signups_from_ip": self._recent_signups_by_ip.get(ip, 0),
            "email_domain_is_disposable": email.split("@")[-1] in {"tempmail.com", "mailinator.com"},
        }


class SimpleRuleFraudModel:
    def predict(self, features: dict) -> float:
        score = 0.0
        if features.get("recent_signups_from_ip", 0) >= 3:
            score += 0.6
        if features.get("email_domain_is_disposable"):
            score += 0.5
        return min(score, 1.0)


class FraudScoringService:
    HIGH_RISK_THRESHOLD = 0.5

    def __init__(self, registry: ModelRegistry, features: FeatureStore, model_version: Optional[str] = None) -> None:
        self._registry = registry
        self._features = features
        self._model_version = model_version

    def score(self, email: str, ip: str) -> float:
        model = self._registry.get("fraud_risk", self._model_version)
        features = self._features.get_features(ip, email)
        return model.predict(features)

    def is_high_risk(self, score: float) -> bool:
        return score >= self.HIGH_RISK_THRESHOLD


# Core service, built through TDD, extended with dependency injection
class SignupService:
    def __init__(self, validator, hasher, fraud_service: FraudScoringService) -> None:
        self._validator = validator
        self._hasher = hasher
        self._fraud_service = fraud_service

    def signup(self, email: str, password: str, ip: str) -> SignupResult:
        self._validator.validate(password)
        self._hasher.hash(password)
        risk_score = self._fraud_service.score(email, ip)
        high_risk = self._fraud_service.is_high_risk(risk_score)
        return SignupResult(email=email, accepted=not high_risk,
                             risk_score=risk_score, flagged_as_high_risk=high_risk)


# Decorator pattern
class SignupServiceComponent(ABC):
    @abstractmethod
    def signup(self, email: str, password: str, ip: str) -> SignupResult: ...


class SignupServiceAdapter(SignupServiceComponent):
    def __init__(self, inner: SignupService) -> None:
        self._inner = inner

    def signup(self, email: str, password: str, ip: str) -> SignupResult:
        return self._inner.signup(email, password, ip)


class SignupServiceDecorator(SignupServiceComponent):
    def __init__(self, wrapped: SignupServiceComponent) -> None:
        self._wrapped = wrapped

    def signup(self, email: str, password: str, ip: str) -> SignupResult:
        return self._wrapped.signup(email, password, ip)


class LoggingSignupDecorator(SignupServiceDecorator):
    def __init__(self, wrapped: SignupServiceComponent, log_sink: list) -> None:
        super().__init__(wrapped)
        self._log = log_sink

    def signup(self, email: str, password: str, ip: str) -> SignupResult:
        try:
            result = super().signup(email, password, ip)
            self._log.append(f"SIGNUP email={email} ip={ip} accepted={result.accepted}")
            return result
        except ValidationError as exc:
            self._log.append(f"SIGNUP email={email} ip={ip} rejected violations={exc.violations}")
            raise


class RateLimitingSignupDecorator(SignupServiceDecorator):
    def __init__(self, wrapped: SignupServiceComponent, max_attempts: int = 5,
                 window_seconds: float = 60.0, clock: Callable[[], float] = time.time) -> None:
        super().__init__(wrapped)
        self._max, self._window, self._clock = max_attempts, window_seconds, clock
        self._attempts: dict = {}

    def signup(self, email: str, password: str, ip: str) -> SignupResult:
        cutoff = self._clock() - self._window
        recent = [t for t in self._attempts.get(ip, []) if t > cutoff]
        if len(recent) >= self._max:
            raise RateLimitedError(f"Too many signup attempts from {ip}")
        recent.append(self._clock())
        self._attempts[ip] = recent
        return super().signup(email, password, ip)


# Visitor pattern
class SignupResultVisitor(ABC):
    @abstractmethod
    def visit_signup_result(self, result: SignupResult) -> None: ...


class ComplianceReportVisitor(SignupResultVisitor):
    def __init__(self) -> None:
        self.flagged_emails: list = []

    def visit_signup_result(self, result: SignupResult) -> None:
        if result.flagged_as_high_risk:
            self.flagged_emails.append(result.email)


class AnalyticsVisitor(SignupResultVisitor):
    def __init__(self) -> None:
        self.total_signups = 0
        self._risk_total = 0.0

    def visit_signup_result(self, result: SignupResult) -> None:
        self.total_signups += 1
        self._risk_total += result.risk_score

    @property
    def average_risk(self) -> float:
        return self._risk_total / self.total_signups if self.total_signups else 0.0


def build_standard_signup_pipeline(factory: AuthProviderFactory, log_sink: list) -> SignupServiceComponent:
    registry = ModelRegistry()
    registry.register("fraud_risk", "v1", SimpleRuleFraudModel())
    features = FeatureStore()
    fraud_service = FraudScoringService(registry, features)

    core = SignupService(factory.create_validator(), factory.create_hasher(), fraud_service)
    logged = LoggingSignupDecorator(SignupServiceAdapter(core), log_sink)
    return RateLimitingSignupDecorator(logged)
```

## Appendix D: Mocking, Stubs and Interface Contracts

```python
import unittest
from unittest.mock import Mock, create_autospec
from signup_system import (
    FraudScoringService, SignupService, StandardAuthProviderFactory,
    SimpleHasher, ValidationError,
)


class SignupServiceMockingTests(unittest.TestCase):
    def setUp(self):
        self.validator = StandardAuthProviderFactory().create_validator()
        self.hasher = SimpleHasher()

    def test_signup_is_accepted_when_fraud_service_reports_low_risk(self):
        fraud_service = Mock(spec=FraudScoringService)
        fraud_service.score.return_value = 0.1
        fraud_service.is_high_risk.return_value = False

        service = SignupService(self.validator, self.hasher, fraud_service)
        result = service.signup("person@example.com", "correcthorse9", "10.0.0.1")

        self.assertTrue(result.accepted)
        fraud_service.score.assert_called_once_with("person@example.com", "10.0.0.1")

    def test_mock_with_spec_enforces_the_real_interface_contract(self):
        fraud_service = Mock(spec=FraudScoringService)
        with self.assertRaises(AttributeError):
            fraud_service.score_the_signup_somehow("x@example.com", "10.0.0.1")

    def test_password_validation_runs_before_the_fraud_service_is_even_called(self):
        fraud_service = Mock(spec=FraudScoringService)
        service = SignupService(self.validator, self.hasher, fraud_service)
        with self.assertRaises(ValidationError):
            service.signup("person@example.com", "weak", "10.0.0.1")
        fraud_service.score.assert_not_called()


class StubFraudScoringService:
    def score(self, email: str, ip: str) -> float:
        return 0.05

    def is_high_risk(self, score: float) -> bool:
        return score >= 0.5


class SignupServiceStubTests(unittest.TestCase):
    def test_stub_produces_a_realistic_low_risk_signup(self):
        validator = StandardAuthProviderFactory().create_validator()
        service = SignupService(validator, SimpleHasher(), StubFraudScoringService())
        result = service.signup("person@example.com", "correcthorse9", "10.0.0.1")
        self.assertTrue(result.accepted)


class AutospecContractTests(unittest.TestCase):
    def test_autospec_catches_a_call_with_the_wrong_number_of_arguments(self):
        fraud_service = create_autospec(FraudScoringService, instance=True)
        with self.assertRaises(TypeError):
            fraud_service.score("only_one_argument")
```

## Appendix E: AI Suggested Edge Cases, Reviewed and Kept

```python
import unittest
from unittest.mock import Mock
from signup_system import (
    FraudScoringService, RateLimitedError, RateLimitingSignupDecorator,
    SignupService, SignupServiceAdapter, SimpleHasher, StandardAuthProviderFactory,
)


class AISuggestedEdgeCaseTests(unittest.TestCase):
    """
    Three AI suggested edge cases, kept after review. A fourth idea,
    fuzzing the password with random byte sequences, was considered and not added:
    SignupService only ever receives a Python str from the form layer in
    this system, so that case cannot occur here and testing it would not
    check anything real.
    """

    def test_very_long_password_is_handled_without_error(self):
        validator = StandardAuthProviderFactory().create_validator()
        validator.validate("a1" * 200)  # must not raise or hang

    def test_password_containing_unicode_characters_is_handled(self):
        validator = StandardAuthProviderFactory().create_validator()
        validator.validate("Correct9Hörse")  # must not raise

    def test_empty_ip_address_does_not_bypass_rate_limiting(self):
        fraud_service = Mock(spec=FraudScoringService)
        fraud_service.score.return_value = 0.1
        fraud_service.is_high_risk.return_value = False
        core = SignupService(StandardAuthProviderFactory().create_validator(), SimpleHasher(), fraud_service)
        decorated = RateLimitingSignupDecorator(SignupServiceAdapter(core), max_attempts=1, clock=lambda: 1000.0)

        decorated.signup("a@example.com", "correcthorse9", "")
        with self.assertRaises(RateLimitedError):
            decorated.signup("b@example.com", "correcthorse9", "")
```
