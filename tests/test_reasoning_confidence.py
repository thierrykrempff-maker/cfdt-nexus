"""Confidence assessment is technical, documentary and structural only."""

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
from NEXUS_CORE.reasoning import ConfidenceEngine, FactExtractor, ReasoningConfidence


NOW = datetime(2026, 7, 21, 14, 0, tzinfo=timezone.utc)


def evidence():
    return Evidence(
        EvidenceId("evidence-confidence"),
        EntityReference(EntityId("subject-confidence"), "person"),
        "status",
        TextEvidenceValue("synthetic"),
        None,
        None,
        Provenance(
            SourceReference(EntityId("source-confidence"), SourceType.SYNTHETIC_FIXTURE, "fixture"),
            AcquisitionMethod.GENERATED,
            NOW,
        ),
        ConfidenceScore(0.9, ConfidenceLevel.HIGH),
        EvidenceQuality.CONSISTENT,
        ValidationStatus.VALID,
        EntityId("producer-confidence-test"),
        (),
        NOW,
    )


def test_no_fact_is_technically_insufficient():
    assessment = ConfidenceEngine().assess(FactExtractor().extract(()), (), ())
    assert assessment.level is ReasoningConfidence.INSUFFICIENT
    assert assessment.technical_score.value == 0.0


def test_validated_fact_produces_high_structural_confidence():
    assessment = ConfidenceEngine().assess(
        FactExtractor().extract((evidence(),)), (), ()
    )
    assert assessment.level is ReasoningConfidence.HIGH
    assert assessment.basis_codes == (
        "TECHNICAL_CONFIDENCE",
        "VALIDATION_COMPLETENESS",
        "STRUCTURAL_COMPLETENESS",
    )


def test_assessment_contains_no_legal_probability_or_decision():
    assessment = ConfidenceEngine().assess(
        FactExtractor().extract((evidence(),)), (), ()
    )
    assert not hasattr(assessment, "legal_probability")
    assert not hasattr(assessment, "decision")
