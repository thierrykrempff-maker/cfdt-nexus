"""End-to-end report, serialization, Protocol and architecture boundaries."""

import ast
from datetime import datetime, timezone
from pathlib import Path

from NEXUS_CORE import (
    AcquisitionMethod,
    ConfidenceLevel,
    ConfidenceScore,
    EntityId,
    EntityReference,
    Evidence,
    EvidenceId,
    EvidenceQuality,
    Provenance,
    SourceReference,
    SourceType,
    TextEvidenceValue,
    ValidationStatus,
)
from NEXUS_CORE.reasoning import (
    FactProducer,
    FactType,
    GenericReasoningPipeline,
    JsonReasoningReporter,
    ReasoningEngine,
    ReasoningReporter,
)


ROOT = Path(__file__).resolve().parents[1]
REASONING = ROOT / "NEXUS_CORE" / "reasoning"
NOW = datetime(2026, 7, 21, 14, 0, tzinfo=timezone.utc)
SUBJECT = EntityReference(EntityId("subject-report"), "person")


def evidence(identifier, value, source):
    return Evidence(
        EvidenceId(f"evidence-{identifier}"),
        SUBJECT,
        "status",
        TextEvidenceValue(value),
        None,
        None,
        Provenance(
            SourceReference(EntityId(f"source-{source}"), SourceType.SYNTHETIC_FIXTURE, "fixture"),
            AcquisitionMethod.GENERATED,
            NOW,
        ),
        ConfidenceScore(0.8, ConfidenceLevel.HIGH),
        EvidenceQuality.CONSISTENT,
        ValidationStatus.VALID,
        EntityId("producer-report-test"),
        (),
        NOW,
    )


def test_pipeline_builds_all_reasoning_sections_without_conclusion():
    report = GenericReasoningPipeline().reason(
        EntityId("report-reasoning-1"),
        (evidence("one", "alpha", "one"), evidence("two", "beta", "two")),
        SUBJECT,
        (FactType("status"), FactType("required_missing")),
        NOW,
    )
    assert len(report.facts.facts) == 2
    assert report.correlations
    assert report.conflicts
    assert report.missing_evidence
    assert report.confidence
    assert len(report.steps) == 7
    assert not hasattr(report, "legal_conclusion")
    assert not hasattr(report, "answer")


def test_report_json_is_deterministic_iso_and_redacts_fact_values():
    secret = "synthetic-sensitive-fact-value"
    report = GenericReasoningPipeline().reason(
        EntityId("report-reasoning-json"),
        (evidence("one", secret, "one"),),
        SUBJECT,
        (FactType("status"),),
        NOW,
    )
    reporter = JsonReasoningReporter()
    first = reporter.render(report)
    assert first == reporter.render(report)
    assert "2026-07-21T14:00:00+00:00" in first
    assert secret not in first
    assert '"schema_version":"1.0"' in first


def test_diagnostics_contain_codes_not_inspected_values():
    secret = "synthetic-secret-for-diagnostic"
    report = GenericReasoningPipeline().reason(
        EntityId("report-diagnostic"),
        (evidence("one", secret, "one"),),
        SUBJECT,
        (FactType("missing_type"),),
        NOW,
    )
    rendered = JsonReasoningReporter().render(report)
    assert secret not in rendered
    assert report.diagnostics[0].code == "REASONING_INCOMPLETE"


def test_public_protocols_are_structurally_implemented():
    pipeline = GenericReasoningPipeline()
    reporter = JsonReasoningReporter()
    assert isinstance(pipeline, ReasoningEngine)
    assert isinstance(pipeline._facts, FactProducer)
    assert isinstance(reporter, ReasoningReporter)


def test_reasoning_has_no_engine_network_database_or_dynamic_import():
    forbidden = {
        "automation",
        "RETIREMENT_PENIBILITY_ENGINE",
        "CCSEMEMORYENGINE",
        "PROTECTION_SOCIALE_ENGINE",
        "requests",
        "urllib",
        "http",
        "socket",
        "ssl",
        "sqlite3",
        "sqlalchemy",
    }
    for path in REASONING.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        roots = set()
        for item in ast.walk(tree):
            if isinstance(item, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in item.names)
            elif isinstance(item, ast.ImportFrom) and item.level == 0 and item.module:
                roots.add(item.module.split(".")[0])
            elif isinstance(item, ast.Call) and isinstance(item.func, ast.Name):
                assert item.func.id not in {"__import__", "eval", "exec"}
        assert not roots & forbidden, path.name


def test_reasoning_sources_are_acyclic_and_python_3_10_compatible():
    paths = tuple(sorted(REASONING.glob("*.py")))
    modules = {path.stem for path in paths}
    graph = {module: set() for module in modules}
    for path in paths:
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
            feature_version=(3, 10),
        )
        for item in ast.walk(tree):
            if isinstance(item, ast.ImportFrom) and item.level == 1 and item.module:
                target = item.module.split(".")[0]
                if target in modules:
                    graph[path.stem].add(target)

    visited = set()
    visiting = set()

    def visit(module):
        assert module not in visiting, f"import cycle involving {module}"
        if module in visited:
            return
        visiting.add(module)
        for dependency in graph[module]:
            visit(dependency)
        visiting.remove(module)
        visited.add(module)

    for module in graph:
        visit(module)
