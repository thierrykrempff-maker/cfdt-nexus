"""Prudent deterministic confidence mapping from values supplied by connectors."""

from __future__ import annotations

from NEXUS_CORE import ConfidenceLevel, ConfidenceScore
from NEXUS_CORE.reasoning import ConfidenceAssessment, ReasoningConfidence

from .models import ConnectorAdapterInput


class ConnectorConfidenceMapper:
    def map(self, source: ConnectorAdapterInput, evidence_count: int,
            diagnostic_count: int) -> ConfidenceAssessment:
        provided = source.response.source_confidence
        if provided is None:
            score = 0.0
            level = ReasoningConfidence.INSUFFICIENT
            technical = ConfidenceLevel.UNKNOWN
        else:
            score = max(0.0, min(1.0, provided))
            if score >= 0.8:
                level, technical = ReasoningConfidence.HIGH, ConfidenceLevel.HIGH
            elif score >= 0.5:
                level, technical = ReasoningConfidence.MODERATE, ConfidenceLevel.MEDIUM
            elif score > 0:
                level, technical = ReasoningConfidence.LIMITED, ConfidenceLevel.LOW
            else:
                level, technical = ReasoningConfidence.INSUFFICIENT, ConfidenceLevel.UNKNOWN
        return ConfidenceAssessment(
            level,
            ConfidenceScore(score, technical),
            evidence_count,
            0,
            0,
            diagnostic_count,
            ("CONNECTOR_PROVIDED_CONFIDENCE",) if provided is not None
            else ("CONNECTOR_CONFIDENCE_MISSING",),
        )
