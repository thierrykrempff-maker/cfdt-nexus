"""Reasoning report construction and deterministic safe export."""

from __future__ import annotations

from datetime import datetime

from ..identifiers import EntityId
from ..privacy import Diagnostic
from ..serialization import to_json
from .models import (
    ConfidenceAssessment,
    Corroboration,
    FactCollection,
    FactCorrelation,
    MissingEvidence,
    ReasoningConflict,
    ReasoningReport,
    ReasoningStep,
)


class ReasoningReportBuilder:
    def build(
        self,
        report_id: EntityId,
        facts: FactCollection,
        correlations: tuple[FactCorrelation, ...],
        corroborations: tuple[Corroboration, ...],
        conflicts: tuple[ReasoningConflict, ...],
        missing_evidence: tuple[MissingEvidence, ...],
        confidence: ConfidenceAssessment,
        steps: tuple[ReasoningStep, ...],
        diagnostics: tuple[Diagnostic, ...],
        created_at: datetime,
    ) -> ReasoningReport:
        return ReasoningReport(
            report_id=report_id,
            facts=facts,
            correlations=correlations,
            corroborations=corroborations,
            conflicts=conflicts,
            missing_evidence=missing_evidence,
            confidence=confidence,
            steps=steps,
            diagnostics=diagnostics,
            created_at=created_at,
        )


class JsonReasoningReporter:
    def render(self, report: ReasoningReport) -> str:
        return to_json(report)
