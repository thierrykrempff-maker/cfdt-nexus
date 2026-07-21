"""Missing Evidence is driven only by explicit technical requirements."""

from datetime import date, datetime, timezone

from NEXUS_CORE import (
    AcquisitionMethod,
    ConfidenceLevel,
    ConfidenceScore,
    EntityId,
    EntityReference,
    Evidence,
    EvidenceId,
    EvidenceQuality,
    Period,
    Provenance,
    SourceReference,
    SourceType,
    TextEvidenceValue,
    ValidationStatus,
)
from NEXUS_CORE.reasoning import (
    FactExtractor,
    FactType,
    MissingEvidenceEngine,
    MissingEvidenceReason,
)


NOW = datetime(2026, 7, 21, 14, 0, tzinfo=timezone.utc)
SUBJECT = EntityReference(EntityId("subject-missing"), "person")


def evidence():
    return Evidence(
        EvidenceId("evidence-present"),
        SUBJECT,
        "present_fact",
        TextEvidenceValue("synthetic"),
        Period(date(2025, 1, 1), date(2025, 6, 30)),
        None,
        Provenance(
            SourceReference(EntityId("source-missing-test"), SourceType.SYNTHETIC_FIXTURE, "fixture"),
            AcquisitionMethod.GENERATED,
            NOW,
        ),
        ConfidenceScore(0.7, ConfidenceLevel.MEDIUM),
        EvidenceQuality.CONSISTENT,
        ValidationStatus.VALID,
        EntityId("producer-missing-test"),
        (),
        NOW,
    )


def test_absent_explicit_requirement_is_reported_without_inventing_evidence():
    facts = FactExtractor().extract((evidence(),))
    missing = MissingEvidenceEngine().identify(
        facts, SUBJECT, (FactType("required_fact"),)
    )
    assert len(missing) == 1
    assert missing[0].reason is MissingEvidenceReason.REQUIRED_FACT_ABSENT
    assert missing[0].blocks_reasoning is True
    assert len(facts.facts) == 1


def test_uncovered_required_period_is_reported():
    facts = FactExtractor().extract((evidence(),))
    missing = MissingEvidenceEngine().identify(
        facts,
        SUBJECT,
        (FactType("present_fact"),),
        Period(date(2025, 1, 1), date(2025, 12, 31)),
    )
    assert missing[0].reason is MissingEvidenceReason.REQUIRED_PERIOD_NOT_COVERED


def test_no_requirements_produce_no_missing_evidence():
    facts = FactExtractor().extract(())
    assert MissingEvidenceEngine().identify(facts, SUBJECT, ()) == ()
