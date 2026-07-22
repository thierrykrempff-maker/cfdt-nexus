"""Offline generic adaptation of already-produced connector snapshots."""

from __future__ import annotations

from NEXUS_CORE import (
    EntityId, EvidenceId, Finding, FindingId, FindingSeverity, FindingStatus,
    FindingType,
)
from NEXUS_CORE.orchestration import (
    EngineCapability, ExecutionContext, ExecutionDiagnostics, ExecutionResult, ExecutionStatus,
)

from .confidence import ConnectorConfidenceMapper
from .documents import ConnectorDocumentMapper
from .evidence import ConnectorEvidenceMapper
from .identity import stable_connector_id
from .metadata import ConnectorMetadataMapper
from .models import (
    ConnectorAdapterDiagnostics, ConnectorAdapterInput, ConnectorAdapterResult,
    ConnectorResponseStatus, ConnectorSourceCategory,
)
from .provenance import ConnectorProvenanceMapper
from .validation import ConnectorAdapterValidator


CONNECTOR_ADAPTATION = EngineCapability("CONNECTOR_SNAPSHOT_ADAPTATION")


class GenericConnectorAdapter:
    """Transform snapshots only; no HTTP, OAuth, pagination or authentication."""

    def __init__(self, source: ConnectorAdapterInput) -> None:
        if not isinstance(source, ConnectorAdapterInput):
            raise TypeError("source must be a ConnectorAdapterInput")
        self._source = source
        self._documents = ConnectorDocumentMapper()
        self._evidence = ConnectorEvidenceMapper()
        self._metadata = ConnectorMetadataMapper()
        self._provenance = ConnectorProvenanceMapper()
        self._confidence = ConnectorConfidenceMapper()
        self._validator = ConnectorAdapterValidator()

    def adapt(self) -> ConnectorAdapterResult:
        source = self._source
        documents = self._documents.map(source)
        evidence = self._evidence.map(source)
        findings = self._findings()
        diagnostics = self._diagnostics()
        provenances = tuple(
            self._provenance.map(source, item) for item in source.response.documents
        ) or (self._provenance.map(source),)
        ignored = (
            ("PAGINATION_ALREADY_RESOLVED",) if source.response.pagination else ()
        )
        result = ConnectorAdapterResult(
            source.descriptor.connector_id,
            source.descriptor.version,
            documents,
            evidence,
            findings,
            provenances,
            self._confidence.map(source, len(evidence), len(diagnostics)),
            diagnostics,
            ignored,
        )
        validation = self._validator.validate(source, result)
        if validation.diagnostics:
            result = ConnectorAdapterResult(
                result.connector_id, result.connector_version, result.documents,
                result.evidence, result.findings, result.provenances, result.confidence,
                result.diagnostics + validation.diagnostics,
                result.ignored_data_codes, result.schema_version,
            )
        return result

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        result = self.adapt()
        output_references = tuple(
            [EntityId(item.document_id.value) for item in result.documents]
            + [EntityId(item.evidence_id.value) for item in result.evidence]
            + [EntityId(item.finding_id.value) for item in result.findings]
        )
        diagnostics = tuple(
            ExecutionDiagnostics(
                item.code, item.category, item.severity,
                EntityId(stable_connector_id("engine", result.connector_id)),
                item.technical_reference,
            )
            for item in result.diagnostics
        )
        failed = (
            self._source.schema_version != "1.0"
            or self._source.response.status is ConnectorResponseStatus.FAILED
        )
        return ExecutionResult(
            EntityId(stable_connector_id(
                "result", context.execution_id.value, self._source.response.response_id
            )),
            EntityId(stable_connector_id("engine", result.connector_id)),
            ExecutionStatus.FAILED if failed else ExecutionStatus.SUCCEEDED,
            (CONNECTOR_ADAPTATION,),
            output_references,
            duration_ms=self._source.response.duration_ms or 0,
            diagnostics=diagnostics,
        )

    def _findings(self) -> tuple[Finding, ...]:
        findings = []
        for item in self._source.response.records:
            if item.explicit_conclusion_code is None or item.explicit_conclusion is None:
                continue
            identity = item.record_id or item.source_document_id or item.record_type
            evidence_id = EvidenceId(stable_connector_id(
                "evidence", self._source.descriptor.connector_id, "record", identity
            ))
            findings.append(Finding(
                FindingId(stable_connector_id(
                    "finding", self._source.descriptor.connector_id, identity
                )),
                FindingType.OBSERVATION,
                FindingSeverity.INFO,
                FindingStatus.OPEN,
                "CONNECTOR_EXPLICIT_CONCLUSION",
                (evidence_id,),
                metadata=(
                    self._metadata.entry(
                        "source_conclusion_code", item.explicit_conclusion_code
                    ),
                    self._metadata.entry(
                        "source_conclusion", item.explicit_conclusion, sensitive=True
                    ),
                ),
            ))
        return tuple(findings)

    def _diagnostics(self) -> tuple[ConnectorAdapterDiagnostics, ...]:
        source = self._source
        diagnostics = []
        if source.schema_version != "1.0":
            diagnostics.append(self._diagnostic(
                "CONNECTOR_SCHEMA_INCOMPATIBLE", "version_incompatible", "high"
            ))
        if source.source.category is ConnectorSourceCategory.UNKNOWN:
            diagnostics.append(self._diagnostic(
                "CONNECTOR_SOURCE_UNKNOWN", "source_unknown", "medium"
            ))
        if source.response.source_confidence is None:
            diagnostics.append(self._diagnostic(
                "CONNECTOR_CONFIDENCE_MISSING", "confidence_missing", "medium"
            ))
        if not source.response.documents and not source.response.records:
            diagnostics.append(self._diagnostic(
                "CONNECTOR_RESPONSE_EMPTY", "data_absent", "low"
            ))
        for index, item in enumerate(source.response.documents):
            reference = EntityId(stable_connector_id(
                "document_input", source.descriptor.connector_id, str(index)
            ))
            if not item.external_id:
                diagnostics.append(self._diagnostic(
                    "CONNECTOR_DOCUMENT_ID_MISSING", "identifier_missing", "medium", reference
                ))
            if item.publication_date is None:
                diagnostics.append(self._diagnostic(
                    "CONNECTOR_DOCUMENT_DATE_MISSING", "date_missing", "low", reference
                ))
            if item.content is None and item.excerpt is None:
                diagnostics.append(self._diagnostic(
                    "CONNECTOR_DOCUMENT_CONTENT_MISSING", "content_missing", "low", reference
                ))
            if not item.document_type:
                diagnostics.append(self._diagnostic(
                    "CONNECTOR_DOCUMENT_TYPE_UNKNOWN", "type_unknown", "medium", reference
                ))
        if source.response.technical_errors:
            diagnostics.append(self._diagnostic(
                "CONNECTOR_TECHNICAL_ERROR_REPORTED", "source_error", "high"
            ))
        if source.response.technical_warnings:
            diagnostics.append(self._diagnostic(
                "CONNECTOR_TECHNICAL_WARNING_REPORTED", "source_warning", "medium"
            ))
        return tuple(diagnostics)

    @staticmethod
    def _diagnostic(code, category, severity, reference=None):
        return ConnectorAdapterDiagnostics(code, category, severity, reference)
