# Unit 12 Seminar: Capstone Project and Review

## Learning Outcomes

- Understand and implement secure coding practices in software development.
- Apply advanced object-oriented principles to solve complex software problems.
- Utilise design patterns to create reusable, maintainable, and flexible code.
- Design software architectures suitable for large-scale systems, ensuring security and robustness.
- Develop software solutions that are adaptable for AI models and efficient for data science tasks.

## General Overview

This seminar is the culmination of the module. The Capstone Project below integrates object-oriented design, creational, structural and behavioural patterns, secure coding, concurrency, test-driven development and an AI-adaptable scoring layer in one system. The second half of the document reviews the key concepts of the module, with each one tied back to where it appears in the project, to support the final assessment and the peer review session.

---

# Part 1: Capstone Project, SupplyChainGuard

## 1.1 Problem Statement and Objectives

Modern software is mostly assembled from third party packages. A single vulnerable dependency can compromise an otherwise well written application, and teams often do not know which versions of which packages they are running or whether any carry known vulnerabilities. This is the problem behind several high profile supply chain incidents, and it is a cybersecurity problem with a data science flavour, since the output is a risk score per dependency.

SupplyChainGuard reads a dependency manifest, looks up known advisories for each dependency, scores the risk, raises alerts on critical findings and produces a report. The objectives are:

1. Treat every manifest as untrusted input and validate it strictly.
2. Restrict scanning to authenticated callers.
3. Fail closed: a dependency that could not be checked is never reported as safe.
4. Keep each concern replaceable (manifest format, advisory source, scoring method, report format, alerting) without editing existing classes.
5. Allow the risk scoring to be swapped from simple rules to a trained model without changing the rest of the system.
6. Scan large manifests efficiently and safely using concurrency.
7. Build it test first, with security and concurrency behaviour covered by tests.

## 1.2 Design and Architecture

The flow of a scan, from the entry point to the report, is shown below.

```
Caller
  |  api key, format, manifest text
  v
ScannerFacade  ------------------>  ApiKeyAuthenticator   (authenticate first)
  |
  |-- ParserFactory.for_format() -> RequirementsParser / JsonManifestParser
  |        (strict validation, size limits, Dependency value objects)
  |
  |-- ThreadPoolExecutor: for each Dependency
  |        |
  |        v
  |   AuditLoggingAdvisorySource
  |        -> CachingAdvisorySource
  |             -> InMemoryAdvisorySource  (or LegacyFeedAdapter)
  |        |
  |        v
  |   ScoringStrategy: MaxSeverity / CountWeighted / ModelScoring
  |                                                   |
  |                          ModelRegistry + FeatureStore + model
  |
  |-- ReportBuilder -> ScanReport (sorted by risk)
  |-- ScanSubject.notify() -> AlertObserver(s) on critical or unverified results
  v
ScanReport.accept(ResultVisitor): TextRenderer / JsonRenderer
```

### Object-oriented principles

- Encapsulation: Dependency is an immutable value object that validates its own name and version on construction, so an invalid dependency cannot exist anywhere in the system. The authenticator keeps its key digests private and exposes only issue_key and authenticate.
- Abstraction: ManifestParser, AdvisorySource, ScoringStrategy, AlertObserver and ResultVisitor are abstract base classes. The facade depends on these abstractions, never on concrete classes.
- Inheritance: the two advisory source decorators share a common base, AdvisorySourceDecorator, which forwards the call by default so that each subclass only adds its own behaviour.
- Polymorphism: any parser, source, scorer or renderer can be substituted for another. The tests rely on this by replacing the real source with a mock.

### Design patterns

Creational
- Factory Method: ParserFactory.for_format chooses the parser from the manifest format. Adding YAML support means adding one class and one dictionary entry.
- Builder: ReportBuilder accumulates results step by step and build() produces an immutable, sorted ScanReport.

Structural
- Adapter: LegacyFeedAdapter makes a third party feed with a different record shape (pkg, ver, cvss, desc) satisfy the AdvisorySource interface, converting CVSS scores to the Severity scale.
- Decorator: CachingAdvisorySource and AuditLoggingAdvisorySource add caching and audit logging to any source, in any order, without modifying it.
- Facade: ScannerFacade gives the presentation layer a single scan method hiding authentication, parsing, concurrency, scoring and alerting.

Behavioural
- Strategy: MaxSeverityScoring, CountWeightedScoring and ModelScoring are interchangeable scoring algorithms.
- Observer: ScanSubject notifies attached AlertObserver objects when a result is critical or unverified. New alert channels (email, chat, ticketing) are added by attaching a new observer.
- Visitor: ScanReport.accept(visitor) lets TextRenderer and JsonRenderer produce different output formats without the result classes knowing about either format.

### Secure coding practices

- Input validation: names and versions are checked against strict allow-list patterns. Manifests are limited to 100,000 bytes and 1,000 dependencies. JSON shape is checked as well as syntax. Malformed lines are reported by line number without echoing their content back, which avoids reflecting attacker controlled text into logs or responses.
- Authentication: API keys are generated with the secrets module, only SHA-256 digests are stored, and comparison uses hmac.compare_digest across every stored digest with no early exit, so response time does not reveal which key matched. Authentication happens before any parsing, so unauthenticated callers cannot probe the parser.
- Exception handling: every error derives from GuardError. Adapter failures are caught and re-raised as AdvisorySourceError with a generic message, so internal details such as hostnames or credentials in a client exception never reach the caller. A test confirms this.
- Fail closed: if an advisory lookup fails, that dependency is recorded as unverified with maximum risk and an alert is raised, rather than being reported as clean.
- Defence against untrusted model output: ModelScoring clamps whatever the model returns to the range 0.0 to 1.0.

### Concurrency

Scanning uses a ThreadPoolExecutor, because lookups against a real advisory source are I/O bound and parallelise well. Shared mutable state is protected: the cache and the audit log each have a lock. The cache lock guards only the dictionary access, not the slow lookup itself, so threads do not queue behind one another. The trade-off is that two threads may occasionally look up the same dependency at the same time, which wastes a lookup but cannot produce a wrong answer. Alerts are raised from the calling thread after the results are gathered, and results come back in input order, which keeps the output deterministic.

### AI and data science adaptability

ModelScoring is one more Strategy, so the rest of the system is unaware of how a score is produced. It obtains a model from a ModelRegistry (named, versioned models, latest by default) and builds model inputs through a FeatureStore, so that training and serving code compute features identically. The included RuleBasedRiskModel is a stand-in with the same predict(features) call shape that a trained model would have. Replacing it with a real model means registering a new version, with no change to the scanner.

## 1.3 Key Challenges and How They Were Addressed

1. Untrusted input. Manifests come from outside the system boundary. The answer was to validate at construction time inside Dependency, so every code path benefits, rather than relying on each caller to remember to validate.
2. A failing dependency must not look safe. A naive design would skip a dependency whose lookup failed. The facade instead fails closed and marks the result unverified.
3. Third party code that cannot be changed. The Adapter keeps the legacy feed's shape out of the domain model, and wraps its exceptions so internals do not leak.
4. Thread safety without serialising everything. Locks are scoped narrowly and the thread pool is created per scan, so no state is shared between scans other than the cache.
5. Testing code that depends on slow or unreliable collaborators. Dependency injection through constructors means every collaborator can be replaced with a Mock using spec, which also checks that the mock matches the real interface.
6. Observers that fail. One broken observer must not stop a scan or hide results, so notification isolates each observer's exceptions. The trade-off is that failures there are silent, which the limitations below note.

## 1.4 Example Run

Scanning a manifest against two known advisories produces the output below, which is the real output of the demo in Appendix C.

```
badlib==1.0.0 risk=0.85 worst=CRITICAL
midlib==2.1.0 risk=0.45 worst=MEDIUM
safelib==3.0.0 risk=0.00 worst=NONE
```

## 1.5 Limitations and Further Work

- Version matching is exact. A real system must evaluate version ranges (for example, affected below 1.4.2).
- The advisory source is in-memory or a stand-in feed. A real deployment would use a vulnerability database and handle network timeouts, retries and rate limits.
- API keys are held in memory. A real deployment needs persistent storage, key rotation, revocation and per-key roles.
- Observer failures are swallowed to protect the scan. A production system should log them to a separate channel.
- The risk model is a rule-based placeholder. Its weights are illustrative, not validated against real incident data.
- The in-memory cache has no expiry, so advisories published after a lookup would not be seen by a long-running process.
- ModelRegistry picks the latest version by sorting version strings, so v10 would sort before v9. Proper version ordering is needed before more than a few versions exist.

---

# Part 2: Review of Key Concepts

## 2.1 Object-Oriented Programming

The four principles solve different problems. Encapsulation protects invariants by hiding state behind a controlled interface. Abstraction lets callers depend on what something does rather than how. Inheritance shares behaviour between related types, but should be used sparingly and with the Liskov Substitution Principle in mind, so that a subclass can be used anywhere its parent is expected. Polymorphism lets one call site work with many implementations. SOLID ties these together: single responsibility (each class here does one thing), open/closed (new formats and scorers are added by extension), Liskov substitution (every parser and source is interchangeable), interface segregation (each ABC has one method), and dependency inversion (the facade depends on abstractions, wired together only in build_default_scanner). A recurring rule of thumb is to favour composition over inheritance, which is why decorators wrap a source rather than subclass every combination.

## 2.2 Design Patterns

Creational patterns control how objects are made (Factory Method, Abstract Factory, Builder). Structural patterns control how objects are composed (Adapter, Bridge, Composite, Decorator, Facade, Proxy). Behavioural patterns control how objects communicate (Strategy, Observer, Visitor). Patterns give a team a shared vocabulary. Each one in the capstone is there because a concrete variation point needed it, and adding a pattern without such a need is itself a code smell.

## 2.3 Concurrency and Parallelism

Concurrency is dealing with many things at once, parallelism is doing many things at once. In Python, threads suit I/O bound work, since the global interpreter lock limits CPU bound speedups, for which processes are the usual answer. The core hazards are race conditions (unsynchronised access to shared state), deadlock (threads waiting on each other in a cycle, prevented by always acquiring locks in a consistent order), and the use of a non-reentrant lock where the same thread may need it twice, which deadlocks against itself. The practical rules are to minimise shared mutable state, keep critical sections short, never hold a lock across slow operations, and prefer immutable data, as the frozen dataclasses here do.

## 2.4 Secure Coding Practices

The core habits are to validate input with allow-lists, never trust data crossing a boundary (including model output), authenticate before doing work, store secrets only as salted or keyed hashes (or, for high entropy API keys, plain SHA-256 digests), compare secrets in constant time, use parameterised queries to prevent SQL injection, apply rate limiting to blunt brute force, fail closed, and return generic error messages while keeping detail in protected logs. Defence in depth means no single control is relied upon.

## 2.5 Refactoring and Code Smells

Refactoring changes structure without changing behaviour, and relies on a test suite to prove that behaviour is unchanged. Common smells include long methods, large classes, duplicated code, long if/elif chains on type, primitive obsession and feature envy. The capstone design avoids several by construction: the format switch is replaced by a Factory Method (removing an if/elif chain on type), raw strings for name and version are replaced by the Dependency value object (removing primitive obsession), and rendering is moved into visitors (removing presentation logic from the data classes). Typical refactorings are Extract Method, Replace Conditional with Polymorphism and Introduce Parameter Object.

## 2.6 Test-Driven Development

TDD follows red, green, refactor: write a failing test, write the minimum code to pass it, then improve the design with the tests as a safety net. Benefits are a design shaped by usage, built-in regression protection, and fewer untested paths. Good unit tests are isolated, fast, deterministic and named after the behaviour they check. Mocks verify interactions, stubs supply canned answers, and Mock(spec=...) or create_autospec ensure a test double still matches the real interface. The suite for this project has 39 tests covering validation, parsing, adapters, decorators, scoring, authentication, the facade, observers, visitors and concurrency, and the main security properties above each have a test.

## 2.7 Quick Revision Table

| Topic | Key idea | Where it appears in the capstone |
|---|---|---|
| Encapsulation | Hide state, protect invariants | Dependency validates itself, authenticator hides digests |
| Abstraction | Depend on interfaces | Five ABCs, facade uses only abstractions |
| Factory Method | Delegate object creation | ParserFactory |
| Builder | Build complex objects stepwise | ReportBuilder |
| Adapter | Make incompatible interfaces fit | LegacyFeedAdapter |
| Decorator | Add behaviour by wrapping | Caching and audit logging sources |
| Facade | One simple entry point | ScannerFacade |
| Strategy | Swap algorithms | Three scoring strategies |
| Observer | Notify without coupling | Alerts on critical findings |
| Visitor | Add operations without changing classes | Text and JSON renderers |
| Thread safety | Protect shared state | Locks on cache, log and alert list |
| Secure coding | Validate, authenticate, fail closed | Parsers, authenticator, facade |
| TDD | Red, green, refactor | 39 tests |

---

## Appendix A: capstone.py

```python
"""
Capstone: SupplyChainGuard, a dependency risk scanner.

Problem: teams pull in third party packages without knowing which versions
carry known vulnerabilities. This tool parses a dependency manifest, looks up
advisories, scores the risk of each dependency and alerts on critical findings.

Concepts demonstrated
- OOP: encapsulation (validated value objects), inheritance and abstraction
  (ABCs), polymorphism (interchangeable parsers, sources, scorers, visitors)
- Creational: Factory Method (parsers), Builder (report)
- Structural: Adapter (legacy feed), Decorator (caching, logging), Facade
- Behavioural: Strategy (scoring), Observer (alerts), Visitor (rendering)
- Secure coding: strict input validation, hashed API keys with constant time
  comparison, fail closed error handling, no internal detail in error messages
- Concurrency: thread pool scanning, lock protected cache
- AI adaptable: ModelRegistry and FeatureStore behind a scoring Strategy
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, Optional


# ----------------------------------------------------------------------
# Domain model and exception hierarchy
# ----------------------------------------------------------------------
class Severity(IntEnum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def from_cvss(cls, score: float) -> "Severity":
        if score >= 9.0:
            return cls.CRITICAL
        if score >= 7.0:
            return cls.HIGH
        if score >= 4.0:
            return cls.MEDIUM
        if score > 0.0:
            return cls.LOW
        return cls.NONE


class GuardError(Exception):
    """Base class: callers can catch one type and never see internals."""


class InputValidationError(GuardError):
    pass


class AuthenticationError(GuardError):
    pass


class AdvisorySourceError(GuardError):
    pass


_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
_VERSION_RE = re.compile(r"^\d+(\.\d+){0,3}$")


@dataclass(frozen=True)
class Dependency:
    """Immutable value object. Invalid state can never be constructed."""

    name: str
    version: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not _NAME_RE.match(self.name):
            raise InputValidationError("Invalid package name")
        if not isinstance(self.version, str) or not _VERSION_RE.match(self.version):
            raise InputValidationError("Invalid package version")


@dataclass(frozen=True)
class Advisory:
    package: str
    affected_version: str
    severity: Severity
    summary: str


# ----------------------------------------------------------------------
# Creational: Factory Method for manifest parsers
# ----------------------------------------------------------------------
MAX_MANIFEST_BYTES = 100_000
MAX_DEPENDENCIES = 1_000


def _check_size(text: str) -> None:
    if not isinstance(text, str):
        raise InputValidationError("Manifest must be text")
    if len(text.encode("utf-8")) > MAX_MANIFEST_BYTES:
        raise InputValidationError("Manifest is too large")


class ManifestParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> list:
        """Return a list of validated Dependency objects."""


class RequirementsParser(ManifestParser):
    """Parses lines of the form name==1.2.3. Blank lines and comments are skipped."""

    def parse(self, text: str) -> list:
        _check_size(text)
        deps = []
        for number, raw in enumerate(text.splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("==")
            if len(parts) != 2:
                # The line number is reported, the content is not echoed back.
                raise InputValidationError(f"Malformed entry on line {number}")
            deps.append(Dependency(parts[0].strip(), parts[1].strip()))
            if len(deps) > MAX_DEPENDENCIES:
                raise InputValidationError("Too many dependencies")
        return deps


class JsonManifestParser(ManifestParser):
    """Parses {"dependencies": {"name": "1.2.3"}}."""

    def parse(self, text: str) -> list:
        _check_size(text)
        try:
            data = json.loads(text)
        except ValueError:
            raise InputValidationError("Manifest is not valid JSON") from None
        block = data.get("dependencies") if isinstance(data, dict) else None
        if not isinstance(block, dict):
            raise InputValidationError("Manifest must contain a dependencies object")
        if len(block) > MAX_DEPENDENCIES:
            raise InputValidationError("Too many dependencies")
        return [Dependency(name, version) for name, version in block.items()]


class ParserFactory:
    _PARSERS = {"requirements": RequirementsParser, "json": JsonManifestParser}

    @classmethod
    def for_format(cls, fmt: str) -> ManifestParser:
        parser = cls._PARSERS.get(fmt)
        if parser is None:
            raise InputValidationError("Unsupported manifest format")
        return parser()


# ----------------------------------------------------------------------
# Advisory sources: Adapter and Decorators (structural)
# ----------------------------------------------------------------------
class AdvisorySource(ABC):
    @abstractmethod
    def lookup(self, dep: Dependency) -> list:
        """Return the advisories that apply to this exact dependency."""


class InMemoryAdvisorySource(AdvisorySource):
    def __init__(self, advisories: list) -> None:
        self._advisories = list(advisories)

    def lookup(self, dep: Dependency) -> list:
        return [a for a in self._advisories
                if a.package == dep.name and a.affected_version == dep.version]


class LegacyVulnerabilityFeed:
    """Stands in for a third party client we cannot change. Different shape on purpose."""

    def __init__(self, records: list) -> None:
        self._records = records

    def fetch(self, package: str) -> list:
        return [r for r in self._records if r["pkg"] == package]


class LegacyFeedAdapter(AdvisorySource):
    def __init__(self, feed: LegacyVulnerabilityFeed) -> None:
        self._feed = feed

    def lookup(self, dep: Dependency) -> list:
        try:
            records = self._feed.fetch(dep.name)
        except Exception:
            # Wrap any client failure so internals never leak to callers.
            raise AdvisorySourceError("Advisory source unavailable") from None
        return [Advisory(r["pkg"], r["ver"], Severity.from_cvss(r["cvss"]), r["desc"])
                for r in records if r["ver"] == dep.version]


class AdvisorySourceDecorator(AdvisorySource):
    def __init__(self, wrapped: AdvisorySource) -> None:
        self._wrapped = wrapped

    def lookup(self, dep: Dependency) -> list:
        return self._wrapped.lookup(dep)


class CachingAdvisorySource(AdvisorySourceDecorator):
    """Thread safe cache. The lock guards the dict only, never the slow lookup."""

    def __init__(self, wrapped: AdvisorySource) -> None:
        super().__init__(wrapped)
        self._cache: dict = {}
        self._lock = threading.Lock()

    def lookup(self, dep: Dependency) -> list:
        with self._lock:
            if dep in self._cache:
                return self._cache[dep]
        result = super().lookup(dep)
        with self._lock:
            self._cache[dep] = result
        return result


class AuditLoggingAdvisorySource(AdvisorySourceDecorator):
    def __init__(self, wrapped: AdvisorySource, sink: list) -> None:
        super().__init__(wrapped)
        self._sink = sink
        self._lock = threading.Lock()

    def lookup(self, dep: Dependency) -> list:
        try:
            result = super().lookup(dep)
        except AdvisorySourceError:
            self._record(f"LOOKUP {dep.name} {dep.version} failed")
            raise
        self._record(f"LOOKUP {dep.name} {dep.version} advisories={len(result)}")
        return result

    def _record(self, message: str) -> None:
        with self._lock:
            self._sink.append(message)


# ----------------------------------------------------------------------
# AI adaptable scoring: Model Registry, Feature Store, Strategy
# ----------------------------------------------------------------------
class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict = {}

    def register(self, name: str, version: str, model: object) -> None:
        self._models.setdefault(name, {})[version] = model

    def get(self, name: str, version: Optional[str] = None) -> object:
        versions = self._models.get(name)
        if not versions:
            raise KeyError(f"No model registered under '{name}'")
        if version is None:
            return versions[sorted(versions)[-1]]
        if version not in versions:
            raise KeyError(f"Model '{name}' has no version '{version}'")
        return versions[version]


class FeatureStore:
    """One place that turns a dependency and its advisories into model features."""

    def features_for(self, dep: Dependency, advisories: list) -> dict:
        return {
            "max_severity": max((a.severity for a in advisories), default=Severity.NONE) / 4,
            "advisory_count": len(advisories),
            "pre_1_0": dep.version.startswith("0."),
        }


class RuleBasedRiskModel:
    """A stand in for a trained model with the same predict(features) call shape."""

    def predict(self, features: dict) -> float:
        score = features["max_severity"] * 0.8
        score += min(features["advisory_count"], 3) * 0.05
        if features["pre_1_0"]:
            score += 0.05
        return min(score, 1.0)


class ScoringStrategy(ABC):
    @abstractmethod
    def score(self, dep: Dependency, advisories: list) -> float:
        """Return a risk score between 0.0 and 1.0."""


class MaxSeverityScoring(ScoringStrategy):
    def score(self, dep: Dependency, advisories: list) -> float:
        return max((a.severity for a in advisories), default=Severity.NONE) / 4


class CountWeightedScoring(ScoringStrategy):
    def score(self, dep: Dependency, advisories: list) -> float:
        return min(sum(a.severity for a in advisories) / 8, 1.0)


class ModelScoring(ScoringStrategy):
    def __init__(self, registry: ModelRegistry, features: FeatureStore,
                 model_name: str = "dependency_risk", model_version: Optional[str] = None) -> None:
        self._registry = registry
        self._features = features
        self._name = model_name
        self._version = model_version

    def score(self, dep: Dependency, advisories: list) -> float:
        model = self._registry.get(self._name, self._version)
        value = model.predict(self._features.features_for(dep, advisories))
        return min(max(float(value), 0.0), 1.0)  # never trust a model output blindly


# ----------------------------------------------------------------------
# Report: Builder and Visitor
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class DependencyResult:
    dependency: Dependency
    advisories: tuple
    risk: float
    verified: bool = True

    @property
    def worst_severity(self) -> Severity:
        return max((a.severity for a in self.advisories), default=Severity.NONE)

    def accept(self, visitor: "ResultVisitor") -> None:
        visitor.visit(self)


@dataclass(frozen=True)
class ScanReport:
    results: tuple

    def accept(self, visitor: "ResultVisitor") -> None:
        for result in self.results:
            result.accept(visitor)


class ReportBuilder:
    def __init__(self) -> None:
        self._results: list = []

    def add(self, result: DependencyResult) -> "ReportBuilder":
        self._results.append(result)
        return self

    def build(self) -> ScanReport:
        return ScanReport(tuple(sorted(self._results, key=lambda r: (-r.risk, r.dependency.name))))


class ResultVisitor(ABC):
    @abstractmethod
    def visit(self, result: DependencyResult) -> None: ...


class TextRenderer(ResultVisitor):
    def __init__(self) -> None:
        self.lines: list = []

    def visit(self, result: DependencyResult) -> None:
        status = "" if result.verified else " [UNVERIFIED]"
        self.lines.append(
            f"{result.dependency.name}=={result.dependency.version} "
            f"risk={result.risk:.2f} worst={result.worst_severity.name}{status}")


class JsonRenderer(ResultVisitor):
    def __init__(self) -> None:
        self._items: list = []

    def visit(self, result: DependencyResult) -> None:
        self._items.append({
            "name": result.dependency.name,
            "version": result.dependency.version,
            "risk": round(result.risk, 2),
            "worst_severity": result.worst_severity.name,
            "verified": result.verified,
        })

    def output(self) -> str:
        return json.dumps(self._items, indent=2)


# ----------------------------------------------------------------------
# Observer: alerts
# ----------------------------------------------------------------------
class AlertObserver(ABC):
    @abstractmethod
    def update(self, result: DependencyResult) -> None: ...


class ScanSubject:
    def __init__(self) -> None:
        self._observers: list = []

    def attach(self, observer: AlertObserver) -> None:
        self._observers.append(observer)

    def notify(self, result: DependencyResult) -> None:
        for observer in self._observers:
            try:
                observer.update(result)
            except Exception:
                pass  # one faulty observer must not break the scan or hide results


class CollectingAlertObserver(AlertObserver):
    def __init__(self) -> None:
        self.alerts: list = []
        self._lock = threading.Lock()

    def update(self, result: DependencyResult) -> None:
        with self._lock:
            self.alerts.append(f"ALERT {result.dependency.name} {result.dependency.version}")


# ----------------------------------------------------------------------
# Secure coding: API key authentication
# ----------------------------------------------------------------------
class ApiKeyAuthenticator:
    """Stores only SHA-256 digests of keys and compares in constant time."""

    def __init__(self) -> None:
        self._digests: list = []

    def issue_key(self) -> str:
        key = secrets.token_urlsafe(32)
        self._digests.append(hashlib.sha256(key.encode()).digest())
        return key

    def authenticate(self, key: object) -> None:
        if not isinstance(key, str) or not key:
            raise AuthenticationError("Invalid credentials")
        candidate = hashlib.sha256(key.encode()).digest()
        matched = False
        for digest in self._digests:  # no early exit, so timing does not reveal position
            matched |= hmac.compare_digest(candidate, digest)
        if not matched:
            raise AuthenticationError("Invalid credentials")


# ----------------------------------------------------------------------
# Facade: the single entry point the presentation layer uses
# ----------------------------------------------------------------------
class ScannerFacade:
    ALERT_THRESHOLD = Severity.CRITICAL

    def __init__(self, authenticator: ApiKeyAuthenticator, source: AdvisorySource,
                 scorer: ScoringStrategy, subject: Optional[ScanSubject] = None,
                 max_workers: int = 4) -> None:
        self._auth = authenticator
        self._source = source
        self._scorer = scorer
        self._subject = subject or ScanSubject()
        self._workers = max_workers

    def scan(self, api_key: object, manifest_format: str, manifest_text: str) -> ScanReport:
        self._auth.authenticate(api_key)
        deps = ParserFactory.for_format(manifest_format).parse(manifest_text)
        with ThreadPoolExecutor(max_workers=self._workers) as pool:
            results = list(pool.map(self._assess, deps))
        builder = ReportBuilder()
        for result in results:
            builder.add(result)
            if result.worst_severity >= self.ALERT_THRESHOLD or not result.verified:
                self._subject.notify(result)
        return builder.build()

    def _assess(self, dep: Dependency) -> DependencyResult:
        try:
            advisories = tuple(self._source.lookup(dep))
        except AdvisorySourceError:
            # Fail closed: a dependency we could not check is treated as maximum risk.
            return DependencyResult(dep, (), 1.0, verified=False)
        return DependencyResult(dep, advisories, self._scorer.score(dep, list(advisories)))


def build_default_scanner(advisories: list, log_sink: list,
                          authenticator: Optional[ApiKeyAuthenticator] = None) -> ScannerFacade:
    """Composition root: the only place concrete classes are wired together."""
    registry = ModelRegistry()
    registry.register("dependency_risk", "v1", RuleBasedRiskModel())
    source = AuditLoggingAdvisorySource(
        CachingAdvisorySource(InMemoryAdvisorySource(advisories)), log_sink)
    scorer = ModelScoring(registry, FeatureStore())
    return ScannerFacade(authenticator or ApiKeyAuthenticator(), source, scorer)
```

## Appendix B: test_capstone.py

```python
import json
import threading
import unittest
from unittest.mock import Mock

from capstone import (
    Advisory, AdvisorySource, AdvisorySourceError, AlertObserver, ApiKeyAuthenticator,
    AuthenticationError, AuditLoggingAdvisorySource, CachingAdvisorySource,
    CollectingAlertObserver, CountWeightedScoring, Dependency, FeatureStore,
    InMemoryAdvisorySource, InputValidationError, JsonManifestParser, JsonRenderer,
    LegacyFeedAdapter, LegacyVulnerabilityFeed, MaxSeverityScoring, ModelRegistry,
    ModelScoring, ParserFactory, RequirementsParser, RuleBasedRiskModel, ScanSubject,
    ScannerFacade, Severity, TextRenderer, build_default_scanner,
)

CRITICAL = Advisory("badlib", "1.0.0", Severity.CRITICAL, "Remote code execution")
MEDIUM = Advisory("midlib", "2.1.0", Severity.MEDIUM, "Information disclosure")


class DomainTests(unittest.TestCase):
    def test_cvss_maps_to_severity_bands(self):
        self.assertEqual(Severity.from_cvss(9.8), Severity.CRITICAL)
        self.assertEqual(Severity.from_cvss(7.5), Severity.HIGH)
        self.assertEqual(Severity.from_cvss(5.0), Severity.MEDIUM)
        self.assertEqual(Severity.from_cvss(0.1), Severity.LOW)
        self.assertEqual(Severity.from_cvss(0.0), Severity.NONE)

    def test_dependency_rejects_bad_names(self):
        for bad in ["", "-leading", "has space", "a;rm -rf", "x" * 101, "../etc"]:
            with self.assertRaises(InputValidationError, msg=bad):
                Dependency(bad, "1.0.0")

    def test_dependency_rejects_bad_versions(self):
        for bad in ["", "latest", "1.0.0; drop", "1..0", "1.2.3.4.5"]:
            with self.assertRaises(InputValidationError, msg=bad):
                Dependency("lib", bad)

    def test_dependency_is_immutable(self):
        dep = Dependency("lib", "1.0.0")
        with self.assertRaises(Exception):
            dep.name = "other"


class ParserTests(unittest.TestCase):
    def test_requirements_parser_reads_entries_and_skips_comments(self):
        deps = RequirementsParser().parse("# comment\n\nbadlib==1.0.0\nmidlib==2.1.0\n")
        self.assertEqual([d.name for d in deps], ["badlib", "midlib"])

    def test_requirements_parser_reports_line_number_without_echoing_content(self):
        with self.assertRaises(InputValidationError) as ctx:
            RequirementsParser().parse("ok==1.0.0\nSECRET_TOKEN_abc\n")
        self.assertIn("line 2", str(ctx.exception))
        self.assertNotIn("SECRET_TOKEN_abc", str(ctx.exception))

    def test_oversized_manifest_rejected(self):
        with self.assertRaises(InputValidationError):
            RequirementsParser().parse("a==1.0\n" * 20000)

    def test_too_many_dependencies_rejected(self):
        text = "\n".join(f"lib{i}==1.0" for i in range(1001))
        with self.assertRaises(InputValidationError):
            RequirementsParser().parse(text)

    def test_non_string_manifest_rejected(self):
        with self.assertRaises(InputValidationError):
            RequirementsParser().parse(b"lib==1.0")

    def test_json_parser_reads_dependencies(self):
        deps = JsonManifestParser().parse(json.dumps({"dependencies": {"badlib": "1.0.0"}}))
        self.assertEqual(deps[0], Dependency("badlib", "1.0.0"))

    def test_json_parser_rejects_invalid_json_and_wrong_shapes(self):
        for bad in ["{not json", "[]", "{}", '{"dependencies": []}']:
            with self.assertRaises(InputValidationError, msg=bad):
                JsonManifestParser().parse(bad)

    def test_json_parser_rejects_non_string_version(self):
        with self.assertRaises(InputValidationError):
            JsonManifestParser().parse('{"dependencies": {"lib": 1}}')

    def test_factory_returns_matching_parser_and_rejects_unknown(self):
        self.assertIsInstance(ParserFactory.for_format("json"), JsonManifestParser)
        with self.assertRaises(InputValidationError):
            ParserFactory.for_format("yaml")


class AdvisorySourceTests(unittest.TestCase):
    def test_in_memory_source_matches_exact_version_only(self):
        source = InMemoryAdvisorySource([CRITICAL])
        self.assertEqual(source.lookup(Dependency("badlib", "1.0.0")), [CRITICAL])
        self.assertEqual(source.lookup(Dependency("badlib", "1.0.1")), [])

    def test_adapter_translates_legacy_records(self):
        feed = LegacyVulnerabilityFeed([{"pkg": "badlib", "ver": "1.0.0", "cvss": 9.8, "desc": "RCE"}])
        result = LegacyFeedAdapter(feed).lookup(Dependency("badlib", "1.0.0"))
        self.assertEqual(result[0].severity, Severity.CRITICAL)

    def test_adapter_hides_client_failure_details(self):
        feed = Mock()
        feed.fetch.side_effect = RuntimeError("db password=hunter2 host=10.0.0.5")
        with self.assertRaises(AdvisorySourceError) as ctx:
            LegacyFeedAdapter(feed).lookup(Dependency("badlib", "1.0.0"))
        self.assertNotIn("hunter2", str(ctx.exception))

    def test_cache_avoids_repeat_lookups(self):
        inner = Mock(spec=AdvisorySource)
        inner.lookup.return_value = []
        cached = CachingAdvisorySource(inner)
        dep = Dependency("lib", "1.0.0")
        cached.lookup(dep)
        cached.lookup(dep)
        inner.lookup.assert_called_once_with(dep)

    def test_logging_decorator_records_success_and_failure(self):
        sink = []
        inner = Mock(spec=AdvisorySource)
        inner.lookup.side_effect = [[CRITICAL], AdvisorySourceError("x")]
        logged = AuditLoggingAdvisorySource(inner, sink)
        logged.lookup(Dependency("badlib", "1.0.0"))
        with self.assertRaises(AdvisorySourceError):
            logged.lookup(Dependency("lib", "1.0.0"))
        self.assertIn("advisories=1", sink[0])
        self.assertIn("failed", sink[1])


class ScoringTests(unittest.TestCase):
    dep = Dependency("badlib", "1.0.0")

    def test_strategies_are_interchangeable_and_bounded(self):
        for strategy in (MaxSeverityScoring(), CountWeightedScoring()):
            self.assertEqual(strategy.score(self.dep, []), 0.0)
            self.assertLessEqual(strategy.score(self.dep, [CRITICAL] * 5), 1.0)

    def test_max_severity_scoring_value(self):
        self.assertEqual(MaxSeverityScoring().score(self.dep, [CRITICAL]), 1.0)

    def test_model_registry_returns_latest_or_named_version(self):
        registry = ModelRegistry()
        registry.register("m", "v1", "old")
        registry.register("m", "v2", "new")
        self.assertEqual(registry.get("m"), "new")
        self.assertEqual(registry.get("m", "v1"), "old")
        with self.assertRaises(KeyError):
            registry.get("missing")
        with self.assertRaises(KeyError):
            registry.get("m", "v9")

    def test_model_scoring_uses_registry_and_feature_store(self):
        registry = ModelRegistry()
        registry.register("dependency_risk", "v1", RuleBasedRiskModel())
        scorer = ModelScoring(registry, FeatureStore())
        self.assertGreater(scorer.score(self.dep, [CRITICAL]), scorer.score(self.dep, []))

    def test_model_output_is_clamped(self):
        model = Mock()
        model.predict.return_value = 7.5
        registry = ModelRegistry()
        registry.register("dependency_risk", "v1", model)
        self.assertEqual(ModelScoring(registry, FeatureStore()).score(self.dep, []), 1.0)
        model.predict.return_value = -3
        self.assertEqual(ModelScoring(registry, FeatureStore()).score(self.dep, []), 0.0)


class AuthTests(unittest.TestCase):
    def test_valid_key_accepted(self):
        auth = ApiKeyAuthenticator()
        auth.authenticate(auth.issue_key())

    def test_invalid_empty_and_non_string_keys_rejected(self):
        auth = ApiKeyAuthenticator()
        auth.issue_key()
        for bad in ["wrong", "", None, 123, b"bytes"]:
            with self.assertRaises(AuthenticationError, msg=repr(bad)):
                auth.authenticate(bad)

    def test_keys_are_not_stored_in_plain_text(self):
        auth = ApiKeyAuthenticator()
        key = auth.issue_key()
        self.assertNotIn(key.encode(), auth._digests)


class FacadeTests(unittest.TestCase):
    def setUp(self):
        self.log = []
        self.auth = ApiKeyAuthenticator()
        self.key = self.auth.issue_key()
        self.scanner = build_default_scanner([CRITICAL, MEDIUM], self.log, self.auth)

    def test_scan_requires_valid_key(self):
        with self.assertRaises(AuthenticationError):
            self.scanner.scan("nope", "requirements", "badlib==1.0.0")

    def test_report_is_sorted_by_risk_highest_first(self):
        report = self.scanner.scan(self.key, "requirements", "safelib==3.0.0\nmidlib==2.1.0\nbadlib==1.0.0")
        self.assertEqual([r.dependency.name for r in report.results], ["badlib", "midlib", "safelib"])

    def test_clean_dependency_has_low_risk(self):
        report = self.scanner.scan(self.key, "requirements", "safelib==3.0.0")
        self.assertLess(report.results[0].risk, 0.1)

    def test_observer_alerts_only_on_critical(self):
        observer = CollectingAlertObserver()
        subject = ScanSubject()
        subject.attach(observer)
        scanner = ScannerFacade(self.auth, InMemoryAdvisorySource([CRITICAL, MEDIUM]),
                                MaxSeverityScoring(), subject)
        scanner.scan(self.key, "requirements", "badlib==1.0.0\nmidlib==2.1.0")
        self.assertEqual(observer.alerts, ["ALERT badlib 1.0.0"])

    def test_faulty_observer_does_not_break_scan(self):
        class Broken(AlertObserver):
            def update(self, result):
                raise RuntimeError("boom")
        subject = ScanSubject()
        subject.attach(Broken())
        scanner = ScannerFacade(self.auth, InMemoryAdvisorySource([CRITICAL]),
                                MaxSeverityScoring(), subject)
        report = scanner.scan(self.key, "requirements", "badlib==1.0.0")
        self.assertEqual(len(report.results), 1)

    def test_source_failure_fails_closed(self):
        source = Mock(spec=AdvisorySource)
        source.lookup.side_effect = AdvisorySourceError("down")
        observer = CollectingAlertObserver()
        subject = ScanSubject()
        subject.attach(observer)
        scanner = ScannerFacade(self.auth, source, MaxSeverityScoring(), subject)
        result = scanner.scan(self.key, "requirements", "lib==1.0.0").results[0]
        self.assertFalse(result.verified)
        self.assertEqual(result.risk, 1.0)
        self.assertEqual(len(observer.alerts), 1)

    def test_malformed_manifest_surfaces_validation_error(self):
        with self.assertRaises(InputValidationError):
            self.scanner.scan(self.key, "requirements", "not a valid line")

    def test_validation_happens_after_authentication(self):
        with self.assertRaises(AuthenticationError):
            self.scanner.scan("nope", "yaml", "garbage")

    def test_visitors_render_the_same_report_differently(self):
        report = self.scanner.scan(self.key, "requirements", "badlib==1.0.0")
        text, js = TextRenderer(), JsonRenderer()
        report.accept(text)
        report.accept(js)
        self.assertIn("badlib==1.0.0", text.lines[0])
        self.assertEqual(json.loads(js.output())[0]["worst_severity"], "CRITICAL")

    def test_audit_log_records_lookups(self):
        self.scanner.scan(self.key, "requirements", "badlib==1.0.0")
        self.assertTrue(any("badlib" in line for line in self.log))


class ConcurrencyTests(unittest.TestCase):
    def test_parallel_scan_of_many_dependencies_is_complete_and_consistent(self):
        auth = ApiKeyAuthenticator()
        key = auth.issue_key()
        scanner = build_default_scanner([CRITICAL], [], auth)
        manifest = "\n".join(f"lib{i}==1.0.0" for i in range(200)) + "\nbadlib==1.0.0"
        report = scanner.scan(key, "requirements", manifest)
        self.assertEqual(len(report.results), 201)
        self.assertEqual(report.results[0].dependency.name, "badlib")

    def test_cache_is_safe_under_concurrent_access(self):
        inner = InMemoryAdvisorySource([CRITICAL])
        cached = CachingAdvisorySource(inner)
        dep = Dependency("badlib", "1.0.0")
        results = []

        def worker():
            for _ in range(200):
                results.append(cached.lookup(dep))

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(results), 1600)
        self.assertTrue(all(r == [CRITICAL] for r in results))

    def test_concurrent_alerts_are_all_recorded(self):
        observer = CollectingAlertObserver()
        subject = ScanSubject()
        subject.attach(observer)
        auth = ApiKeyAuthenticator()
        key = auth.issue_key()
        scanner = ScannerFacade(auth, InMemoryAdvisorySource([CRITICAL]), MaxSeverityScoring(), subject)
        scanner.scan(key, "requirements", "badlib==1.0.0")
        self.assertEqual(len(observer.alerts), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

## Appendix C: demo_capstone.py

```python
from capstone import *

advisories = [
    Advisory("badlib", "1.0.0", Severity.CRITICAL, "Remote code execution"),
    Advisory("midlib", "2.1.0", Severity.MEDIUM, "Information disclosure"),
]
auth = ApiKeyAuthenticator()
key = auth.issue_key()
log = []
scanner = build_default_scanner(advisories, log, auth)
report = scanner.scan(key, "requirements", "safelib==3.0.0\nmidlib==2.1.0\nbadlib==1.0.0\n")
renderer = TextRenderer()
report.accept(renderer)
print("\n".join(renderer.lines))
```
