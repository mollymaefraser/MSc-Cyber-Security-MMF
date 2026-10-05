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
