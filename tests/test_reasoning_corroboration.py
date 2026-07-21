"""Corroboration is structural compatibility across distinct sources."""

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
    CorroborationEngine,
    CorroborationStrength,
    FactCorrelationEngine,
    FactExtractor,
)


NOW = datetime(2026, 7, 21, 14, 0, tzinfo=timezone.utc)


def evidence(identifier, value="same", source=None, period=None):
    source = source or identifier
    period = period or Period(date(2025, 1, 1), date(2025, 12, 31))
    return Evidence(
        EvidenceId(f"evidence-{identifier}"),
        EntityReference(EntityId("subject-corroboration"), "person"),
        "status",
        TextEvidenceValue(value),
        period,
        None,
        Provenance(
            SourceReference(EntityId(f"source-{source}"), SourceType.SYNTHETIC_FIXTURE, "fixture"),
            AcquisitionMethod.GENERATED,
            NOW,
        ),
        ConfidenceScore(0.7, ConfidenceLevel.MEDIUM),
        EvidenceQuality.CONSISTENT,
        ValidationStatus.VALID,
        EntityId("producer-corroboration-test"),
        (),
        NOW,
    )


def identify(items):
    facts = FactExtractor().extract(tuple(items))
    correlations = FactCorrelationEngine().correlate(facts)
    return CorroborationEngine().identify(facts, correlations)


def test_matching_facts_from_distinct_sources_are_corroborated():
    found = identify((evidence("one"), evidence("two")))
    assert len(found) == 1
    assert found[0].strength is CorroborationStrength.TWO_DISTINCT_SOURCES
    assert len(found[0].fact_references) == 2


def test_same_source_is_not_counted_as_corroboration():
    assert identify((evidence("one", source="shared"), evidence("two", source="shared"))) == ()


def test_different_values_are_not_corroborated():
    assert identify((evidence("one"), evidence("two", value="different"))) == ()
