"""Generic classification pipeline for already-detected documentary situations."""

from __future__ import annotations

from datetime import datetime

from ..conflicts import EvidenceConflict
from ..evidence import Evidence
from ..evidence_graph import EvidenceGraph
from ..findings import Finding
from ..identifiers import EntityId
from ..reasoning.models import Fact, ReasoningReport
from .classification import ResolutionClassifier
from .coherence import CoherenceEvaluator
from .models import ResolutionDiagnostic, ResolutionReport
from .report import ResolutionReportBuilder


class GenericConflictResolutionEngine:
    """Classify and explain; never decide, rank, recommend or arbitrate."""

    def __init__(self) -> None:
        self._classifier = ResolutionClassifier()
        self._coherence = CoherenceEvaluator()
        self._reports = ResolutionReportBuilder()

    def resolve(
        self,
        report_id: EntityId,
        reasoning_report: ReasoningReport,
        created_at: datetime,
        evidence_graph: EvidenceGraph | None = None,
        evidence: tuple[Evidence, ...] = (),
        findings: tuple[Finding, ...] = (),
        conflicts: tuple[EvidenceConflict, ...] = (),
        facts: tuple[Fact, ...] = (),
    ) -> ResolutionReport:
        candidates, classifications = self._classifier.classify(
            reasoning_report, evidence_graph, findings, conflicts, facts
        )
        coherence = self._coherence.evaluate(
            reasoning_report, evidence_graph, evidence, conflicts, facts
        )
        diagnostics = self._diagnostics(reasoning_report)
        return self._reports.build(
            report_id,
            reasoning_report.report_id,
            classifications,
            candidates,
            diagnostics,
            coherence,
            created_at,
        )

    @staticmethod
    def _diagnostics(report: ReasoningReport) -> tuple[ResolutionDiagnostic, ...]:
        diagnostics = [
            ResolutionDiagnostic(
                "EXPECTED_EVIDENCE_ABSENT",
                "missing_evidence",
                "high" if item.blocks_reasoning else "medium",
                (item.missing_id,),
                item.expected_fact_type.code,
                "SUPPORTS_STRUCTURAL_COMPLETENESS",
            )
            for item in report.missing_evidence
        ]
        if report.conflicts:
            diagnostics.append(
                ResolutionDiagnostic(
                    "CONFLICT_REMAINS_UNRESOLVED",
                    "documentary_conflict",
                    "medium",
                    tuple(item.conflict_id for item in report.conflicts),
                )
            )
        if not diagnostics:
            diagnostics.append(
                ResolutionDiagnostic(
                    "RESOLUTION_CLASSIFICATION_COMPLETE",
                    "documentary_resolution",
                    "info",
                )
            )
        return tuple(diagnostics)
