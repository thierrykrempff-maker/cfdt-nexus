"""Official explicit bridge from Expert Paie reports to Nexus Core models."""

from __future__ import annotations

from datetime import datetime

from automation.contracts import ExpertReport, ReportStatus
from automation.expert_facades.payroll import PAYROLL_EXPERT_ID
from NEXUS_CORE import (
    AnalysisRequest,
    DomainSelection,
    EntityId,
    EntityReference,
    Evidence,
    Period,
)
from NEXUS_CORE.orchestration import (
    EngineCapability,
    ExecutionContext,
    ExecutionDiagnostics,
    ExecutionResult,
    ExecutionStatus,
)
from NEXUS_CORE.reasoning import FactCollection, FactExtractor

from ._identity import stable_payroll_id
from .evidence import PayrollEvidenceMapper
from .findings import PayrollFindingMapper
from .metadata import PayrollMetadataMapper
from .models import PayrollAdapterDiagnostics, PayrollAdapterResult
from .recommendations import PayrollRecommendationMapper


PAYROLL_ADAPTATION = EngineCapability("PAYROLL_RESULT_ADAPTATION")


class PayrollAdapter:
    """Translate an already-produced Expert Paie report without executing rules."""

    def __init__(
        self,
        report: ExpertReport,
        subject: EntityReference,
        produced_at: datetime,
        period: Period | None = None,
    ) -> None:
        if not isinstance(report, ExpertReport):
            raise TypeError("report must be an ExpertReport")
        if report.producer != PAYROLL_EXPERT_ID:
            raise ValueError("report producer must identify Expert Paie")
        self._report = report
        self._subject = subject
        self._produced_at = produced_at
        self._period = period
        self._metadata = PayrollMetadataMapper()
        self._evidence = PayrollEvidenceMapper(self._metadata)
        self._findings = PayrollFindingMapper(self._evidence, self._metadata)
        self._recommendations = PayrollRecommendationMapper(self._metadata)

    def adapt(self) -> PayrollAdapterResult:
        return PayrollAdapterResult(
            self._evidence.map(
                self._report, self._subject, self._produced_at, self._period
            ),
            self._findings.map(self._report, self._period),
            self._recommendations.map(self._report),
            self._evidence.map_documents(self._report),
            self._diagnostics(),
            self._report.schema_version,
        )

    def produce_evidence(self, request: AnalysisRequest) -> tuple[Evidence, ...]:
        if DomainSelection.PAYROLL not in request.domains:
            return ()
        return self.adapt().evidence

    def produce_findings(self, request: AnalysisRequest):
        if DomainSelection.PAYROLL not in request.domains:
            return ()
        return self.adapt().findings

    def produce_recommendations(self, request: AnalysisRequest):
        if DomainSelection.PAYROLL not in request.domains:
            return ()
        return self.adapt().recommendations

    def extract(self, evidence: tuple[Evidence, ...]) -> FactCollection:
        return FactExtractor().extract(evidence)

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        adapted = self.adapt()
        output_references = tuple(
            [EntityId(item.evidence_id.value) for item in adapted.evidence]
            + [EntityId(item.finding_id.value) for item in adapted.findings]
            + [EntityId(item.recommendation_id.value) for item in adapted.recommendations]
        )
        diagnostics = tuple(
            ExecutionDiagnostics(
                item.code,
                item.category,
                item.severity,
                engine_reference=EntityId("adapter-payroll"),
                technical_reference=item.technical_reference,
            )
            for item in adapted.diagnostics
        )
        status = (
            ExecutionStatus.FAILED
            if self._report.schema_version != "1.0"
            else ExecutionStatus.SUCCEEDED
        )
        return ExecutionResult(
            EntityId(stable_payroll_id("result", context.execution_id.value, self._report.report_id)),
            EntityId("adapter-payroll"),
            status,
            (PAYROLL_ADAPTATION,),
            output_references,
            diagnostics=diagnostics,
        )

    def _diagnostics(self) -> tuple[PayrollAdapterDiagnostics, ...]:
        diagnostics = []
        reference = EntityId(stable_payroll_id("report", self._report.report_id))
        if self._report.schema_version != "1.0":
            diagnostics.append(
                PayrollAdapterDiagnostics(
                    "PAYROLL_SCHEMA_INCOMPATIBLE",
                    "version_incompatible",
                    "high",
                    reference,
                )
            )
        if not self._report.findings and not self._report.source_evidence:
            diagnostics.append(
                PayrollAdapterDiagnostics(
                    "PAYROLL_DATA_ABSENT", "data_absent", "medium", reference
                )
            )
        if self._report.status in {ReportStatus.DRAFT, ReportStatus.PARTIAL}:
            diagnostics.append(
                PayrollAdapterDiagnostics(
                    "PAYROLL_DATA_INCOMPLETE", "data_incomplete", "medium", reference
                )
            )
        if self._report.warnings or self._report.errors:
            diagnostics.append(
                PayrollAdapterDiagnostics(
                    "PAYROLL_SOURCE_DIAGNOSTICS_PRESENT",
                    "source_diagnostics",
                    "medium",
                    reference,
                )
            )
        return tuple(diagnostics)
