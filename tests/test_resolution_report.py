"""Resolution reports serialize deterministically and expose safe diagnostics."""

from datetime import datetime, timezone

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
from NEXUS_CORE.conflict_resolution import (
    GenericConflictResolutionEngine,
    JsonResolutionReporter,
    ResolutionReporter,
)
from NEXUS_CORE.reasoning import FactType, GenericReasoningPipeline


NOW = datetime(2026, 7, 21, 15, 0, tzinfo=timezone.utc)
SUBJECT = EntityReference(EntityId("subject-resolution-report"), "person")


def report(secret, required):
    evidence = Evidence(
        EvidenceId("evidence-resolution-report"),
        SUBJECT,
        "status",
        TextEvidenceValue(secret),
        None,
        None,
        Provenance(
            SourceReference(EntityId("source-resolution-report"), SourceType.SYNTHETIC_FIXTURE, "fixture"),
            AcquisitionMethod.GENERATED,
            NOW,
        ),
        ConfidenceScore(0.7, ConfidenceLevel.MEDIUM),
        EvidenceQuality.CONSISTENT,
        ValidationStatus.VALID,
        EntityId("producer-resolution-report"),
        (),
        NOW,
    )
    reasoning = GenericReasoningPipeline().reason(
        EntityId("reasoning-report-input"),
        (evidence,),
        SUBJECT,
        required,
        NOW,
    )
    return GenericConflictResolutionEngine().resolve(
        EntityId("resolution-report-output"), reasoning, NOW
    )


def test_json_is_deterministic_iso_dated_and_versioned():
    value = report("synthetic-value", (FactType("status"),))
    reporter = JsonResolutionReporter()
    first = reporter.render(value)
    assert first == reporter.render(value)
    assert "2026-07-21T15:00:00+00:00" in first
    assert '"schema_version":"1.0"' in first
    assert isinstance(reporter, ResolutionReporter)


def test_diagnostics_never_reproduce_inspected_values():
    secret = "synthetic-sensitive-inspected-value"
    value = report(secret, (FactType("status"), FactType("missing_period")))
    rendered = JsonResolutionReporter().render(value)
    assert secret not in rendered
    assert value.diagnostics[0].expected_evidence_type == "missing_period"
    assert value.diagnostics[0].usefulness_code == "SUPPORTS_STRUCTURAL_COMPLETENESS"
    assert not hasattr(value.diagnostics[0], "message")
    assert not hasattr(value.diagnostics[0], "actual_value")


def test_report_summary_contains_counts_not_a_decision():
    value = report("synthetic-value", (FactType("status"),))
    assert value.summary.classification_count == len(value.classifications)
    assert value.summary.coherence_score == value.coherence.overall
    assert not hasattr(value.summary, "decision")
    assert not hasattr(value.summary, "winner")
