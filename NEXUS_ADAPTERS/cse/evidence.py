"""CSE minutes and semantic snapshots to Nexus Core evidence."""

from __future__ import annotations

from datetime import datetime

from automation.cse_memory.document_models import DocumentRecord
from NEXUS_CORE import (
    AcquisitionMethod, ConfidentialityLevel, CustomEvidenceValue, DocumentId,
    DocumentMetadata, DocumentReference, DocumentSource, DocumentType, EntityId,
    EntityReference, Evidence, EvidenceId, Provenance, SourceReference, SourceType,
)

from ._identity import stable_cse_id
from .meeting import CSEMeetingMapper
from .metadata import CSEMetadataMapper
from .models import CSEMeetingSnapshot, CSEVoteSnapshot
from .votes import CSEVoteMapper


class CSEEvidenceMapper:
    def __init__(self, metadata: CSEMetadataMapper | None = None) -> None:
        self._metadata = metadata or CSEMetadataMapper()
        self._meetings = CSEMeetingMapper(self._metadata)
        self._votes = CSEVoteMapper(self._metadata)

    def map_documents(self, records: tuple[DocumentRecord, ...]) -> tuple[DocumentReference, ...]:
        return tuple(self._document(record) for record in records)

    def map(self, records: tuple[DocumentRecord, ...], meetings: tuple[CSEMeetingSnapshot, ...],
            votes: tuple[CSEVoteSnapshot, ...], subject: EntityReference,
            produced_at: datetime) -> tuple[Evidence, ...]:
        document_evidence = tuple(
            self._document_evidence(record, subject, produced_at) for record in records
        )
        meeting_evidence = tuple(
            self._meetings.map(meeting, subject, produced_at) for meeting in meetings
        )
        vote_evidence = tuple(
            self._votes.map(vote, subject, produced_at)[0] for vote in votes
        )
        return document_evidence + meeting_evidence + vote_evidence

    def _document(self, record: DocumentRecord) -> DocumentReference:
        source = SourceReference(
            EntityId(stable_cse_id("source", record.source_relative_path, record.source_sha256)),
            SourceType.CSE_ARCHIVE,
            "CSE_MEMORY_DOCUMENT",
        )
        entries = (
            self._metadata.sensitive("source_modified_at", record.source_modified_at),
            self._metadata.technical("document_version", record.schema_version),
            self._metadata.technical("document_family", record.detected_family),
            self._metadata.technical("source_size_bytes", record.source_size_bytes),
        )
        return DocumentReference(
            DocumentId(stable_cse_id("document", record.document_id)),
            DocumentType.CSE_MINUTES,
            DocumentSource(source),
            DocumentMetadata(DocumentType.CSE_MINUTES, title="CSE_MINUTES", entries=entries),
            ConfidentialityLevel.CONFIDENTIAL,
        )

    def _document_evidence(self, record: DocumentRecord, subject: EntityReference,
                           produced_at: datetime) -> Evidence:
        return Evidence(
            EvidenceId(stable_cse_id("evidence", "document", record.document_id)),
            subject,
            "cse_minutes_document",
            CustomEvidenceValue(
                "cse_minutes_document",
                (
                    self._metadata.technical("extraction_status", record.extraction_status),
                    self._metadata.technical("text_length", record.text_length),
                    self._metadata.technical("warning_count", len(record.warnings)),
                ),
            ),
            None,
            self._document(record),
            Provenance(
                self._document(record).source.reference,
                AcquisitionMethod.IMPORT,
                self._metadata.parsed_datetime(record.imported_at, produced_at),
                EntityId(stable_cse_id("trace", "document", record.document_id)),
            ),
            self._metadata.confidence(1.0 if record.extraction_status == "extracted" else 0.5),
            self._metadata.quality(record.extraction_status),
            self._metadata.validation(record.extraction_status),
            EntityId("adapter-cse"),
            (),
            produced_at,
            ConfidentialityLevel.CONFIDENTIAL,
        )
