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
