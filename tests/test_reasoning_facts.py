"""Fact extraction must remain a faithful one-to-one Evidence projection."""

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
from NEXUS_CORE.reasoning import FactExtractor


NOW = datetime(2026, 7, 21, 14, 0, tzinfo=timezone.utc)


def make_evidence(identifier="one", fact_type="employment_status", value="synthetic"):
    provenance = Provenance(
        SourceReference(EntityId(f"source-{identifier}"), SourceType.SYNTHETIC_FIXTURE, "fixture"),
        AcquisitionMethod.GENERATED,
        NOW,
    )
    return Evidence(
        EvidenceId(f"evidence-{identifier}"),
        EntityReference(EntityId("subject-pseudo-reasoning"), "person"),
        fact_type,
        TextEvidenceValue(value),
        Period(date(2025, 1, 1), date(2025, 12, 31)),
        None,
        provenance,
        ConfidenceScore(0.8, ConfidenceLevel.HIGH),
        EvidenceQuality.CONSISTENT,
        ValidationStatus.VALID,
        EntityId("producer-reasoning-test"),
        (),
        NOW,
    )


def test_extraction_is_one_to_one_and_invents_no_fact():
    evidence = (make_evidence("one"), make_evidence("two"))
    facts = FactExtractor().extract(evidence)
    assert len(facts.facts) == len(evidence)
    assert {fact.source_evidence for fact in facts.facts} == {
        item.evidence_id for item in evidence
    }


def test_fact_preserves_value_period_provenance_and_confidence():
    evidence = make_evidence()
    fact = FactExtractor().extract((evidence,)).facts[0]
    assert fact.value is evidence.value
    assert fact.period is evidence.period
    assert fact.provenance is evidence.provenance
    assert fact.confidence is evidence.confidence


def test_identical_evidence_is_idempotent():
    evidence = make_evidence()
    facts = FactExtractor().extract((evidence, evidence))
    assert len(facts.facts) == 1


def test_fact_identifier_is_deterministic_and_technical():
    evidence = make_evidence()
    first = FactExtractor().extract((evidence,)).facts[0]
    second = FactExtractor().extract((evidence,)).facts[0]
    assert first.fact_id == second.fact_id
    assert first.fact_id.value.startswith("fact-")
