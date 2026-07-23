"""Deterministic sequencing of the generic structural reasoning stages."""

from __future__ import annotations

from datetime import datetime

from ..entities import EntityReference
from ..evidence import Evidence
from ..identifiers import EntityId
from ..periods import Period
from ..privacy import Diagnostic
from .confidence import ConfidenceEngine
from .conflicts import ConflictEngine
from .correlation import FactCorrelationEngine
from .corroboration import CorroborationEngine
from .facts import FactExtractor
from .missing_evidence import MissingEvidenceEngine
from .models import FactType, ReasoningReport, ReasoningStep
from .report import ReasoningReportBuilder


class GenericReasoningPipeline:
    """Build a reasoning trace without answering, deciding or arbitrating."""

    def __init__(self) -> None:
        self._facts = FactExtractor()
        self._correlations = FactCorrelationEngine()
        self._corroborations = CorroborationEngine()
        self._conflicts = ConflictEngine()
        self._missing = MissingEvidenceEngine()
        self._confidence = ConfidenceEngine()
        self._reports = ReasoningReportBuilder()

    def reason(
        self,
        report_id: EntityId,
        evidence: tuple[Evidence, ...],
        subject: EntityReference,
        required_fact_types: tuple[FactType, ...],
        created_at: datetime,
        required_period: Period | None = None,
    ) -> ReasoningReport:
        facts = self._facts.extract(evidence)
        correlations = self._correlations.correlate(facts)
        corroborations = self._corroborations.identify(facts, correlations)
        conflicts = self._conflicts.detect(facts, correlations)
        missing = self._missing.identify(
            facts, subject, required_fact_types, required_period
        )
        confidence = self._confidence.assess(facts, conflicts, missing)
        diagnostics = self._diagnostics(conflicts, missing)
        steps = (
            ReasoningStep(1, "EXTRACT_FACTS", output_references=self._fact_ids(facts)),
            ReasoningStep(
                2,
                "CORRELATE_FACTS",
                input_references=self._fact_ids(facts),
                output_references=tuple(item.correlation_id for item in correlations),
            ),
            ReasoningStep(
                3,
                "IDENTIFY_CORROBORATIONS",
                output_references=tuple(item.corroboration_id for item in corroborations),
            ),
            ReasoningStep(
                4,
                "DETECT_CONFLICTS",
                output_references=tuple(item.conflict_id for item in conflicts),
            ),
            ReasoningStep(
                5,
                "IDENTIFY_MISSING_EVIDENCE",
                output_references=tuple(item.missing_id for item in missing),
            ),
            ReasoningStep(6, "ASSESS_TECHNICAL_CONFIDENCE"),
            ReasoningStep(7, "BUILD_REASONING_REPORT", output_references=(report_id,)),
        )
        return self._reports.build(
            report_id,
            facts,
            correlations,
            corroborations,
            conflicts,
            missing,
            confidence,
            steps,
            diagnostics,
            created_at,
        )

    @staticmethod
    def _fact_ids(facts):
        return tuple(fact.fact_id for fact in facts.facts)

    @staticmethod
    def _diagnostics(conflicts, missing):
        diagnostics = []
        if conflicts:
            diagnostics.append(
                Diagnostic("STRUCTURAL_CONFLICTS", "reasoning_conflict", "medium")
            )
        if missing:
            diagnostics.append(
                Diagnostic("REASONING_INCOMPLETE", "missing_evidence", "high")
            )
        if not diagnostics:
            diagnostics.append(
                Diagnostic("REASONING_BUILT", "structural_reasoning", "info")
            )
        return tuple(diagnostics)
