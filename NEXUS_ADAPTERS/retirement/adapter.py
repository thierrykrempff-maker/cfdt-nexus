"""Official explicit bridge from Retirement outputs to Nexus Core models."""

from __future__ import annotations

from NEXUS_CORE import AnalysisRequest, DomainSelection, EntityId, Evidence
from NEXUS_CORE.orchestration import (
    EngineCapability, ExecutionContext, ExecutionDiagnostics, ExecutionResult, ExecutionStatus,
)
from NEXUS_CORE.reasoning import FactCollection, FactExtractor

from ._identity import stable_retirement_id
from .career import RetirementCareerMapper
from .conflicts import RetirementConflictMapper
from .evidence import RetirementEvidenceMapper
from .findings import RetirementFindingMapper
from .models import RetirementAdapterDiagnostics, RetirementAdapterInput, RetirementAdapterResult
from .recommendations import RetirementRecommendationMapper


RETIREMENT_ADAPTATION = EngineCapability("RETIREMENT_RESULT_ADAPTATION")


class RetirementAdapter:
    """Translate immutable Retirement outputs without executing domain rules."""

    def __init__(self, source: RetirementAdapterInput) -> None:
        if not isinstance(source, RetirementAdapterInput):
            raise TypeError("source must be a RetirementAdapterInput")
        self._source = source
        self._evidence = RetirementEvidenceMapper()
        self._findings = RetirementFindingMapper()
        self._recommendations = RetirementRecommendationMapper()
        self._career = RetirementCareerMapper()
        self._conflicts = RetirementConflictMapper()

    def adapt(self) -> RetirementAdapterResult:
        source = self._source
        reconstruction_bundle = (
            source.reconstruction.proposed_evidence
            if source.reconstruction is not None else None
        )
        evidence_bundle = source.evidence_bundle or reconstruction_bundle
        evidence = self._evidence.map_bundle(
            evidence_bundle, source.subject, source.produced_at
        ) + self._evidence.map_foundation(
            source.report.report_id, source.report.evidence_used,
            source.subject, source.produced_at,
        ) + self._evidence.map_expert(source.expert_report, source.subject, source.produced_at)
        conflicts, candidates = self._conflicts.map(
            source.reconstruction, source.reasoning_outcome
        )
        return RetirementAdapterResult(
            evidence,
            self._findings.map(
                source.report, source.reconstruction, source.reasoning_outcome,
                source.expert_report,
            ),
            self._recommendations.map(source.report, source.expert_report),
            self._evidence.map_documents(evidence_bundle),
            self._career.map(source.reconstruction, source.subject),
            conflicts,
            candidates,
            self._diagnostics(),
            source.source_schema_version,
        )

    def produce_evidence(self, request: AnalysisRequest) -> tuple[Evidence, ...]:
        if DomainSelection.RETIREMENT_PENIBILITY not in request.domains:
            return ()
        return self.adapt().evidence

    def produce_findings(self, request: AnalysisRequest):
        if DomainSelection.RETIREMENT_PENIBILITY not in request.domains:
            return ()
        return self.adapt().findings

    def produce_recommendations(self, request: AnalysisRequest):
        if DomainSelection.RETIREMENT_PENIBILITY not in request.domains:
            return ()
        return self.adapt().recommendations

    def extract(self, evidence: tuple[Evidence, ...]) -> FactCollection:
        return FactExtractor().extract(evidence)

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        adapted = self.adapt()
        outputs = tuple(
            [EntityId(item.evidence_id.value) for item in adapted.evidence]
            + [EntityId(item.finding_id.value) for item in adapted.findings]
            + [EntityId(item.recommendation_id.value) for item in adapted.recommendations]
            + [item.conflict_id for item in adapted.reasoning_conflicts]
            + [item.candidate_id for item in adapted.resolution_candidates]
        )
        diagnostics = tuple(
            ExecutionDiagnostics(
                item.code, item.category, item.severity,
                engine_reference=EntityId("adapter-retirement"),
                technical_reference=item.technical_reference,
            )
            for item in adapted.diagnostics
        )
        status = ExecutionStatus.SUCCEEDED
        if self._source.source_schema_version != "1.0":
            status = ExecutionStatus.FAILED
        return ExecutionResult(
            EntityId(stable_retirement_id(
                "result", context.execution_id.value, self._source.report.report_id
            )),
            EntityId("adapter-retirement"),
            status,
            (RETIREMENT_ADAPTATION,),
            outputs,
            diagnostics=diagnostics,
        )

    def _diagnostics(self) -> tuple[RetirementAdapterDiagnostics, ...]:
        source = self._source
        reference = EntityId(stable_retirement_id("report", source.report.report_id))
        diagnostics = []
        if source.source_schema_version != "1.0":
            diagnostics.append(RetirementAdapterDiagnostics(
                "RETIREMENT_SCHEMA_INCOMPATIBLE", "version_incompatible", "high", reference
            ))
        if source.expert_report is not None and source.expert_report.schema_version != "1.0":
            diagnostics.append(RetirementAdapterDiagnostics(
                "RETIREMENT_EXPERT_SCHEMA_INCOMPATIBLE", "version_incompatible", "high", reference
            ))
        if not source.report.evidence_used and source.evidence_bundle is None:
            diagnostics.append(RetirementAdapterDiagnostics(
                "RETIREMENT_DATA_ABSENT", "data_absent", "medium", reference
            ))
        if source.report.missing_information:
            diagnostics.append(RetirementAdapterDiagnostics(
                "RETIREMENT_DATA_INCOMPLETE", "data_incomplete", "medium", reference
            ))
        if source.reconstruction is None:
            diagnostics.append(RetirementAdapterDiagnostics(
                "RETIREMENT_RECONSTRUCTION_ABSENT", "career_incomplete", "low", reference
            ))
        elif any(item.start_date.value is None for item in source.reconstruction.proposed_periods):
            diagnostics.append(RetirementAdapterDiagnostics(
                "RETIREMENT_PERIOD_INCOMPLETE", "career_incomplete", "medium", reference
            ))
        return tuple(diagnostics)
