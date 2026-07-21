"""Deterministic construction and serialization of resolution reports."""

from __future__ import annotations

from datetime import datetime

from ..identifiers import EntityId
from ..serialization import to_json
from .models import (
    CoherenceAssessment,
    ResolutionCandidate,
    ResolutionClassification,
    ResolutionDiagnostic,
    ResolutionReport,
    ResolutionSummary,
)


class ResolutionReportBuilder:
    def build(
        self,
        report_id: EntityId,
        source_reasoning_report: EntityId,
        classifications: tuple[ResolutionClassification, ...],
        candidates: tuple[ResolutionCandidate, ...],
        diagnostics: tuple[ResolutionDiagnostic, ...],
        coherence: CoherenceAssessment,
        created_at: datetime,
    ) -> ResolutionReport:
        summary = ResolutionSummary(
            len(classifications),
            len(candidates),
            len(diagnostics),
            tuple(item.category for item in classifications),
            coherence.overall,
        )
        return ResolutionReport(
            report_id,
            source_reasoning_report,
            classifications,
            candidates,
            diagnostics,
            coherence,
            summary,
            created_at,
        )


class JsonResolutionReporter:
    def render(self, report: ResolutionReport) -> str:
        return to_json(report)
