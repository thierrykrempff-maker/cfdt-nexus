"""Reasoning conflicts are detected and explained but never arbitrated."""

from datetime import date, datetime, timezone

import pytest

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
    ConflictEngine,
    FactCorrelationEngine,
    FactExtractor,
    ReasoningConflict,
)


NOW = datetime(2026, 7, 21, 14, 0, tzinfo=timezone.utc)


def evidence(identifier, value, period=None):
    return Evidence(
        EvidenceId(f"evidence-{identifier}"),
        EntityReference(EntityId("subject-conflict"), "person"),
        "status",
        TextEvidenceValue(value),
        period or Period(date(2025, 1, 1), date(2025, 12, 31)),
        None,
        Provenance(
            SourceReference(EntityId(f"source-{identifier}"), SourceType.SYNTHETIC_FIXTURE, "fixture"),
            AcquisitionMethod.GENERATED,
            NOW,
        ),
        ConfidenceScore(0.7, ConfidenceLevel.MEDIUM),
        EvidenceQuality.CONSISTENT,
        ValidationStatus.VALID,
        EntityId("producer-conflict-test"),
        (),
        NOW,
    )


def detect(items):
    facts = FactExtractor().extract(tuple(items))
    correlations = FactCorrelationEngine().correlate(facts)
    return ConflictEngine().detect(facts, correlations)


def test_incompatible_values_for_overlapping_period_are_detected():
    conflicts = detect((evidence("one", "alpha"), evidence("two", "beta")))
    assert len(conflicts) == 1
    assert conflicts[0].explanation.code == "FACT_VALUE_MISMATCH"


def test_conflict_never_selects_or_arbitrates_a_fact():
    conflict = detect((evidence("one", "alpha"), evidence("two", "beta")))[0]
    assert conflict.arbitrated is False
    assert conflict.selected_fact is None


def test_non_overlapping_periods_are_not_declared_conflicting():
    first = evidence("one", "alpha", Period(date(2024, 1, 1), date(2024, 12, 31)))
    second = evidence("two", "beta", Period(date(2025, 1, 1), date(2025, 12, 31)))
    assert detect((first, second)) == ()


def test_model_rejects_attempted_arbitration():
    original = detect((evidence("one", "alpha"), evidence("two", "beta")))[0]
    with pytest.raises(ValueError, match="never be arbitrated"):
        ReasoningConflict(
            original.conflict_id,
            original.fact_references,
            original.explanation,
            original.period,
            arbitrated=True,
        )
