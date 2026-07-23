"""Official translation-only bridge from CSE Memory to Nexus Core V3."""

from __future__ import annotations

from NEXUS_CORE import AnalysisRequest, DomainSelection, EntityId, Evidence
from NEXUS_CORE.orchestration import (
    EngineCapability, ExecutionContext, ExecutionDiagnostics, ExecutionResult, ExecutionStatus,
)
from NEXUS_CORE.reasoning import ConflictExplanation, FactCollection, FactExtractor, ReasoningConflict

from ._identity import stable_cse_id
from .evidence import CSEEvidenceMapper
from .findings import CSEFindingMapper
from .metadata import CSEMetadataMapper
from .models import CSEAdapterDiagnostics, CSEAdapterInput, CSEAdapterResult
from .recommendations import CSERecommendationMapper


CSE_ADAPTATION = EngineCapability("CSE_MEMORY_RESULT_ADAPTATION")


class CSEAdapter:
    """Translate injected CSE records; never import, parse or analyze documents."""

    def __init__(self, source: CSEAdapterInput) -> None:
        if not isinstance(source, CSEAdapterInput):
            raise TypeError("source must be a CSEAdapterInput")
        self._source = source
        self._metadata = CSEMetadataMapper()
        self._evidence = CSEEvidenceMapper(self._metadata)
        self._findings = CSEFindingMapper()
        self._recommendations = CSERecommendationMapper()

    def adapt(self) -> CSEAdapterResult:
        source = self._source
        evidence = self._evidence.map(
            source.documents, source.meetings, source.votes,
            source.subject, source.produced_at,
        )
        conflicts = self._conflicts()
        return CSEAdapterResult(
            evidence,
            self._findings.map(
                source.decisions, source.votes, source.subject, source.produced_at
            ),
            self._recommendations.map(source.decisions),
            self._evidence.map_documents(source.documents),
            (),
            conflicts,
            self._metadata.assessment(source.metadata_records, len(evidence), len(conflicts)),
            self._diagnostics(),
            source.source_schema_version,
        )

    def produce_evidence(self, request: AnalysisRequest) -> tuple[Evidence, ...]:
        if DomainSelection.CSE not in request.domains:
            return ()
        return self.adapt().evidence

    def produce_findings(self, request: AnalysisRequest):
        if DomainSelection.CSE not in request.domains:
            return ()
        return self.adapt().findings

    def produce_recommendations(self, request: AnalysisRequest):
        if DomainSelection.CSE not in request.domains:
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
        )
        diagnostics = tuple(
            ExecutionDiagnostics(
                item.code, item.category, item.severity,
                engine_reference=EntityId("adapter-cse"),
                technical_reference=item.technical_reference,
            )
            for item in adapted.diagnostics
        )
        status = (
            ExecutionStatus.SUCCEEDED
            if self._source.source_schema_version == "1.0"
            else ExecutionStatus.FAILED
        )
        return ExecutionResult(
            EntityId(stable_cse_id("result", context.execution_id.value)),
            EntityId("adapter-cse"),
            status,
            (CSE_ADAPTATION,),
            outputs,
            diagnostics=diagnostics,
        )

    def _conflicts(self) -> tuple[ReasoningConflict, ...]:
        conflicts = []
        for record in self._source.metadata_records:
            for index, _ in enumerate(record.conflicts):
                refs = (
                    EntityId(stable_cse_id("fact", record.metadata_record_id, str(index), "left")),
                    EntityId(stable_cse_id("fact", record.metadata_record_id, str(index), "right")),
                )
                conflicts.append(ReasoningConflict(
                    EntityId(stable_cse_id("conflict", record.metadata_record_id, str(index))),
                    refs,
                    ConflictExplanation("CSE_METADATA_CONFLICT", "DOCUMENT_METADATA", refs),
                    None,
                ))
        return tuple(conflicts)

    def _diagnostics(self) -> tuple[CSEAdapterDiagnostics, ...]:
        source = self._source
        diagnostics = []
        if source.source_schema_version != "1.0":
            diagnostics.append(CSEAdapterDiagnostics(
                "CSE_SCHEMA_INCOMPATIBLE", "version_incompatible", "high",
                EntityId(stable_cse_id("input", source.source_schema_version)),
            ))
        if not source.documents and not source.meetings:
            diagnostics.append(CSEAdapterDiagnostics(
                "CSE_DATA_ABSENT", "data_absent", "medium"
            ))
        if any(record.extraction_status != "extracted" for record in source.documents):
            diagnostics.append(CSEAdapterDiagnostics(
                "CSE_DOCUMENT_INCOMPLETE", "document_incomplete", "medium"
            ))
        if any(record.schema_version != "1.0" for record in source.documents):
            diagnostics.append(CSEAdapterDiagnostics(
                "CSE_DOCUMENT_SCHEMA_INCOMPATIBLE", "version_incompatible", "high"
            ))
        return tuple(diagnostics)
