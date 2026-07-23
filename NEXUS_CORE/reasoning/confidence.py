"""Technical, documentary and structural confidence assessment only."""

from __future__ import annotations

from ..quality import ConfidenceLevel, ConfidenceScore, ValidationStatus
from .models import (
    ConfidenceAssessment,
    FactCollection,
    MissingEvidence,
    ReasoningConfidence,
    ReasoningConflict,
)


class ConfidenceEngine:
    def assess(
        self,
        facts: FactCollection,
        conflicts: tuple[ReasoningConflict, ...],
        missing_evidence: tuple[MissingEvidence, ...],
    ) -> ConfidenceAssessment:
        fact_count = len(facts.facts)
        validated = sum(
            fact.validation_status is ValidationStatus.VALID for fact in facts.facts
        )
        average_confidence = (
            sum(fact.confidence.value for fact in facts.facts) / fact_count
            if fact_count
            else 0.0
        )
        validation_ratio = validated / fact_count if fact_count else 0.0
        structural_factor = 1.0 / (1 + len(conflicts) + len(missing_evidence))
        score = (
            round((average_confidence + validation_ratio + structural_factor) / 3, 6)
            if fact_count
            else 0.0
        )
        level = self._level(fact_count, score, conflicts, missing_evidence)
        return ConfidenceAssessment(
            level=level,
            technical_score=ConfidenceScore(score, self._core_level(score)),
            fact_count=fact_count,
            validated_fact_count=validated,
            conflict_count=len(conflicts),
            missing_evidence_count=len(missing_evidence),
            basis_codes=(
                "TECHNICAL_CONFIDENCE",
                "VALIDATION_COMPLETENESS",
                "STRUCTURAL_COMPLETENESS",
            ),
        )

    @staticmethod
    def _level(fact_count, score, conflicts, missing_evidence):
        if not fact_count or missing_evidence:
            return ReasoningConfidence.INSUFFICIENT
        if conflicts or score < 0.5:
            return ReasoningConfidence.LIMITED
        if score < 0.8:
            return ReasoningConfidence.MODERATE
        return ReasoningConfidence.HIGH

    @staticmethod
    def _core_level(score: float) -> ConfidenceLevel:
        if score == 0:
            return ConfidenceLevel.UNKNOWN
        if score < 0.5:
            return ConfidenceLevel.LOW
        if score < 0.8:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.HIGH
