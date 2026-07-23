"""Immutable connector snapshots and generic adaptation results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from NEXUS_CORE import DocumentReference, Evidence, Finding, Provenance
from NEXUS_CORE.identifiers import EntityId
from NEXUS_CORE.reasoning import ConfidenceAssessment


MetadataScalar = str | int | float | bool | date | datetime | None
MetadataItems = tuple[tuple[str, MetadataScalar], ...]


class ConnectorCapability(str, Enum):
    DOCUMENTS = "DOCUMENTS"
    RECORDS = "RECORDS"
    SEARCH_RESULTS = "SEARCH_RESULTS"
    EXPLICIT_CONCLUSIONS = "EXPLICIT_CONCLUSIONS"


class ConnectorSourceCategory(str, Enum):
    LEGISLATION = "LEGISLATION"
    REGULATION = "REGULATION"
    CASE_LAW = "CASE_LAW"
    ADMINISTRATIVE_DOCTRINE = "ADMINISTRATIVE_DOCTRINE"
    INDEPENDENT_AUTHORITY = "INDEPENDENT_AUTHORITY"
    COLLECTIVE_AGREEMENT = "COLLECTIVE_AGREEMENT"
    COMPANY_AGREEMENT = "COMPANY_AGREEMENT"
    SOCIAL_SECURITY_BODY = "SOCIAL_SECURITY_BODY"
    INTERNAL_DOCUMENT = "INTERNAL_DOCUMENT"
    OTHER_OFFICIAL = "OTHER_OFFICIAL"
    UNKNOWN = "UNKNOWN"


class ConnectorResponseStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    EMPTY = "EMPTY"


@dataclass(frozen=True, slots=True)
class ConnectorDescriptor:
    connector_id: str
    version: str
    capabilities: tuple[ConnectorCapability, ...]


@dataclass(frozen=True, slots=True)
class ConnectorSourceSnapshot:
    source_id: str
    label_code: str
    category: ConnectorSourceCategory
    official: bool
    source_url: str | None = None
    metadata: MetadataItems = ()


@dataclass(frozen=True, slots=True)
class ConnectorDocumentSnapshot:
    external_id: str | None
    source_id: str
    document_type: str
    title: str | None = None
    official_reference: str | None = None
    publication_date: date | None = None
    updated_at: datetime | None = None
    version: str | None = None
    author: str | None = None
    source_url: str | None = None
    language: str | None = None
    content: str | None = None
    excerpt: str | None = None
    fingerprint: str | None = None
    validity_status: str | None = None
    metadata: MetadataItems = ()


@dataclass(frozen=True, slots=True)
class ConnectorRecordSnapshot:
    record_id: str | None
    record_type: str
    source_document_id: str | None = None
    explicit_conclusion_code: str | None = None
    explicit_conclusion: str | None = None
    confidence_score: float | None = None
    metadata: MetadataItems = ()


@dataclass(frozen=True, slots=True)
class ConnectorQuerySnapshot:
    query_id: str
    query_code: str
    parameters: MetadataItems = ()


@dataclass(frozen=True, slots=True)
class ConnectorResponseSnapshot:
    response_id: str
    status: ConnectorResponseStatus
    documents: tuple[ConnectorDocumentSnapshot, ...] = ()
    records: tuple[ConnectorRecordSnapshot, ...] = ()
    technical_warnings: tuple[str, ...] = ()
    technical_errors: tuple[str, ...] = ()
    source_confidence: float | None = None
    pagination: MetadataItems = ()
    duration_ms: int | None = None


@dataclass(frozen=True, slots=True)
class ConnectorAdapterInput:
    descriptor: ConnectorDescriptor
    source: ConnectorSourceSnapshot
    query: ConnectorQuerySnapshot
    response: ConnectorResponseSnapshot
    acquired_at: datetime
    schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class ConnectorAdapterDiagnostics:
    code: str
    category: str
    severity: str
    technical_reference: EntityId | None = None
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        for value in (self.code, self.category, self.severity):
            if not value or not value.replace("_", "").isalnum():
                raise ValueError("diagnostics require neutral technical codes")


@dataclass(frozen=True, slots=True)
class ConnectorAdapterResult:
    connector_id: str
    connector_version: str
    documents: tuple[DocumentReference, ...]
    evidence: tuple[Evidence, ...]
    findings: tuple[Finding, ...]
    provenances: tuple[Provenance, ...]
    confidence: ConfidenceAssessment
    diagnostics: tuple[ConnectorAdapterDiagnostics, ...]
    ignored_data_codes: tuple[str, ...] = ()
    schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class ConnectorValidationReport:
    valid: bool
    structural_violations: tuple[str, ...]
    diagnostics: tuple[ConnectorAdapterDiagnostics, ...]
    deterministic: bool
    serializable: bool
    schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class ConnectorAdapterReport:
    connector_id: str
    connector_version: str
    received_document_count: int
    received_record_count: int
    evidence_count: int
    document_reference_count: int
    finding_count: int
    diagnostics: tuple[ConnectorAdapterDiagnostics, ...]
    ignored_data_codes: tuple[str, ...]
    status: str
    duration_ms: int | None
    schema_version: str = "1.0"
