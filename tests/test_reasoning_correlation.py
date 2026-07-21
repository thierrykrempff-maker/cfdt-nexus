"""Fact correlations link related references without merging their values."""

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
from NEXUS_CORE.reasoning import FactCorrelationEngine, FactExtractor


NOW = datetime(2026, 7, 21, 14, 0, tzinfo=timezone.utc)


def evidence(identifier, subject="subject-a", fact_type="status", value="synthetic"):
    return Evidence(
        EvidenceId(f"evidence-{identifier}"),
        EntityReference(EntityId(subject), "person"),
        fact_type,
        TextEvidenceValue(value),
        None,
        None,
        Provenance(
            SourceReference(EntityId(f"source-{identifier}"), SourceType.SYNTHETIC_FIXTURE, "fixture"),
            AcquisitionMethod.GENERATED,
            NOW,
        ),
        ConfidenceScore(0.7, ConfidenceLevel.MEDIUM),
        EvidenceQuality.CONSISTENT,
        ValidationStatus.VALID,
        EntityId("producer-correlation-test"),
        (),
        NOW,
    )


def test_correlation_groups_same_subject_and_fact_type_by_links_only():
    facts = FactExtractor().extract((evidence("one"), evidence("two", value="other")))
    correlations = FactCorrelationEngine().correlate(facts)
    assert len(correlations) == 1
    assert correlations[0].fact_references == tuple(
        sorted((fact.fact_id for fact in facts.facts), key=lambda item: item.value)
    )
    assert len(facts.facts) == 2


def test_different_subjects_are_not_correlated():
    facts = FactExtractor().extract((evidence("one"), evidence("two", subject="subject-b")))
    assert FactCorrelationEngine().correlate(facts) == ()


def test_different_fact_types_are_not_correlated():
    facts = FactExtractor().extract((evidence("one"), evidence("two", fact_type="other_type")))
    assert FactCorrelationEngine().correlate(facts) == ()
