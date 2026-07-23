"""Coherence scores remain technical, bounded and reproducible."""

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
from NEXUS_CORE.conflict_resolution import CoherenceEvaluator
from NEXUS_CORE.reasoning import FactType, GenericReasoningPipeline


NOW = datetime(2026, 7, 21, 15, 0, tzinfo=timezone.utc)
SUBJECT = EntityReference(EntityId("subject-coherence"), "person")


def evidence(identifier, value, source):
    return Evidence(
        EvidenceId(f"evidence-coherence-{identifier}"),
        SUBJECT,
        "status",
        TextEvidenceValue(value),
        None,
        None,
        Provenance(
            SourceReference(EntityId(f"source-coherence-{source}"), SourceType.SYNTHETIC_FIXTURE, "fixture"),
            AcquisitionMethod.GENERATED,
            NOW,
        ),
        ConfidenceScore(0.8, ConfidenceLevel.HIGH),
        EvidenceQuality.CONSISTENT,
        ValidationStatus.VALID,
        EntityId("producer-coherence"),
        (),
        NOW,
    )


def reasoning(values, required=(FactType("status"),)):
    items = tuple(evidence(str(index), value, str(index)) for index, value in enumerate(values))
    return GenericReasoningPipeline().reason(
        EntityId("reasoning-coherence"), items, SUBJECT, required, NOW
    )


def test_coherence_is_bounded_deterministic_and_documentary_only():
    report = reasoning(("alpha", "alpha"))
    evaluator = CoherenceEvaluator()
    first = evaluator.evaluate(report)
    assert first == evaluator.evaluate(report)
    assert all(
        0.0 <= score <= 1.0
        for score in (
            first.temporal,
            first.documentary,
            first.corroboration,
            first.provenance,
            first.completeness,
            first.overall,
        )
    )
    assert not hasattr(first, "legal_probability")
    assert not hasattr(first, "recommended_evidence")


def test_conflict_reduces_documentary_coherence():
    coherent = CoherenceEvaluator().evaluate(reasoning(("alpha", "alpha")))
    conflicting = CoherenceEvaluator().evaluate(reasoning(("alpha", "beta")))
    assert conflicting.documentary < coherent.documentary


def test_missing_evidence_reduces_completeness():
    complete = CoherenceEvaluator().evaluate(reasoning(("alpha",)))
    incomplete = CoherenceEvaluator().evaluate(
        reasoning(("alpha",), (FactType("status"), FactType("missing")))
    )
    assert incomplete.completeness < complete.completeness
