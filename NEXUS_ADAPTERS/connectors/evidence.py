"""Generic connector documents and records to Core evidence."""

from __future__ import annotations

from NEXUS_CORE import (
    ConfidentialityLevel, CustomEvidenceValue, EntityId, EntityReference, Evidence,
    EvidenceId, EvidenceQuality, TextEvidenceValue, ValidationStatus,
)

from .documents import ConnectorDocumentMapper
from .identity import stable_connector_id
from .metadata import ConnectorMetadataMapper
from .models import ConnectorAdapterInput, ConnectorDocumentSnapshot, ConnectorRecordSnapshot
from .provenance import ConnectorProvenanceMapper


class ConnectorEvidenceMapper:
    def __init__(self) -> None:
        self._documents = ConnectorDocumentMapper()
        self._metadata = ConnectorMetadataMapper()
        self._provenance = ConnectorProvenanceMapper()

    def map(self, source: ConnectorAdapterInput) -> tuple[Evidence, ...]:
        subject = EntityReference(
            EntityId(stable_connector_id(
                "connector_subject", source.descriptor.connector_id, source.source.source_id
            )),
            "official_source",
        )
        documents = tuple(
            self._document(source, item, subject) for item in source.response.documents
        )
        records = tuple(
            self._record(source, item, subject) for item in source.response.records
        )
        return documents + records

    def _document(self, source: ConnectorAdapterInput, item: ConnectorDocumentSnapshot,
                  subject: EntityReference) -> Evidence:
        identity = ConnectorDocumentMapper._identity_material(item)
        value = (
            TextEvidenceValue(item.content)
            if item.content is not None
            else TextEvidenceValue(item.excerpt)
            if item.excerpt is not None
            else CustomEvidenceValue(
                "connector_document_metadata",
                (self._metadata.entry("content_available", False),),
            )
        )
        return Evidence(
            EvidenceId(stable_connector_id(
                "evidence", source.descriptor.connector_id, "document", identity
            )),
            subject,
            "connector_document",
            value,
            None,
            self._documents.map_one(source, item),
            self._provenance.map(source, item),
            ConnectorConfidenceMapperProxy.score(source.response.source_confidence),
            EvidenceQuality.CONSISTENT if item.external_id and item.title else EvidenceQuality.INCOMPLETE,
            ValidationStatus.VALID if item.external_id else ValidationStatus.PENDING,
            EntityId(stable_connector_id("producer", source.descriptor.connector_id)),
            self._metadata.map(item.metadata),
            source.acquired_at,
            ConfidentialityLevel.PUBLIC if source.source.official else ConfidentialityLevel.INTERNAL,
        )

    def _record(self, source: ConnectorAdapterInput, item: ConnectorRecordSnapshot,
                subject: EntityReference) -> Evidence:
        identity = item.record_id or item.source_document_id or item.record_type
        return Evidence(
            EvidenceId(stable_connector_id(
                "evidence", source.descriptor.connector_id, "record", identity
            )),
            subject,
            "connector_record",
            CustomEvidenceValue(
                "connector_record",
                (self._metadata.entry("record_type", item.record_type),),
            ),
            None,
            None,
            self._provenance.map(source),
            ConnectorConfidenceMapperProxy.score(item.confidence_score),
            EvidenceQuality.CONSISTENT if item.record_id else EvidenceQuality.INCOMPLETE,
            ValidationStatus.VALID if item.record_id else ValidationStatus.PENDING,
            EntityId(stable_connector_id("producer", source.descriptor.connector_id)),
            self._metadata.map(item.metadata),
            source.acquired_at,
            ConfidentialityLevel.PUBLIC if source.source.official else ConfidentialityLevel.INTERNAL,
        )


class ConnectorConfidenceMapperProxy:
    """Evidence-level score using only the supplied connector value."""

    @staticmethod
    def score(value):
        from NEXUS_CORE import ConfidenceLevel, ConfidenceScore

        if value is None:
            return ConfidenceScore(0.0, ConfidenceLevel.UNKNOWN)
        score = max(0.0, min(1.0, value))
        level = (
            ConfidenceLevel.HIGH if score >= 0.8 else
            ConfidenceLevel.MEDIUM if score >= 0.5 else
            ConfidenceLevel.LOW if score > 0 else ConfidenceLevel.UNKNOWN
        )
        return ConfidenceScore(score, level)
