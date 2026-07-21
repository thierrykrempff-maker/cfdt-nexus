"""Immutable metadata models for future synthetic career imports.

No model stores document content. Original declared values remain separate
from normalized values and every record retains explicit provenance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ImportDocumentType(str, Enum):
    """Supported future document families, without parser implementations."""

    CAREER_STATEMENT = "CAREER_STATEMENT"
    PAYSLIP = "PAYSLIP"
    EMPLOYMENT_CONTRACT = "EMPLOYMENT_CONTRACT"
    EMPLOYMENT_AMENDMENT = "EMPLOYMENT_AMENDMENT"
    EMPLOYER_CERTIFICATE = "EMPLOYER_CERTIFICATE"
    KELIO_EXPORT = "KELIO_EXPORT"
    NIBELIS_EXPORT = "NIBELIS_EXPORT"
    C2P_DOCUMENT = "C2P_DOCUMENT"
    ATMP_DOCUMENT = "ATMP_DOCUMENT"
    SOCIAL_SECURITY_DOCUMENT = "SOCIAL_SECURITY_DOCUMENT"
    INEOS_DOCUMENT = "INEOS_DOCUMENT"
    OTHER = "OTHER"


class ImportConfidence(str, Enum):
    """Qualitative source confidence without percentage."""

    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ImportStatus(str, Enum):
    """Lifecycle status for an in-memory synthetic batch."""

    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    NORMALIZED = "NORMALIZED"
    CONFLICTED = "CONFLICTED"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    REJECTED = "REJECTED"


class ImportIssueType(str, Enum):
    """Structural validation issues permitted in LOT 7."""

    REQUIRED_FIELD = "REQUIRED_FIELD"
    INVALID_DATE_FORMAT = "INVALID_DATE_FORMAT"
    CHRONOLOGICAL_ORDER = "CHRONOLOGICAL_ORDER"
    INCOHERENT_PERIOD = "INCOHERENT_PERIOD"
    DUPLICATE = "DUPLICATE"
    OVERLAP = "OVERLAP"
    UNKNOWN_VALUE = "UNKNOWN_VALUE"
    INCOMPLETE_DOCUMENT = "INCOMPLETE_DOCUMENT"


class ImportConflictType(str, Enum):
    """Preserved incompatibilities between imported metadata."""

    INCOMPATIBLE_DATES = "INCOMPATIBLE_DATES"
    INCOMPATIBLE_CLASSIFICATIONS = "INCOMPATIBLE_CLASSIFICATIONS"
    INCOMPATIBLE_SCHEDULES = "INCOMPATIBLE_SCHEDULES"
    INCOMPATIBLE_EMPLOYERS = "INCOMPATIBLE_EMPLOYERS"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    DIFFERENT_DOCUMENTS = "DIFFERENT_DOCUMENTS"
    DIFFERENT_VERSIONS = "DIFFERENT_VERSIONS"


class ImportReportView(str, Enum):
    """Employee and expert projections of an import report."""

    EMPLOYEE_VIEW = "EMPLOYEE_VIEW"
    EXPERT_VIEW = "EXPERT_VIEW"


@dataclass(frozen=True)
class ImportSource:
    """Declared origin for a future import operation."""

    source_id: str
    document_type: ImportDocumentType
    internal_document_id: str
    imported_at: str
    version: str
    origin: str
    confidence: ImportConfidence = ImportConfidence.UNKNOWN


@dataclass(frozen=True)
class ImportProvenance:
    """Provenance retained on every imported record."""

    source_id: str
    document_type: ImportDocumentType
    internal_document_id: str
    imported_at: str
    version: str
    origin: str
    confidence: ImportConfidence


@dataclass(frozen=True)
class ImportDocument:
    """Metadata-only document declaration with no path or content."""

    document_id: str
    source: ImportSource
    title: str
    complete: bool = True
    declared_record_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ImportedCareerRecord:
    """Generic original record linked to an existing career-event type."""

    record_id: str
    career_event_type: str
    original_values: tuple[tuple[str, str | None], ...]
    provenance: ImportProvenance


@dataclass(frozen=True)
class ImportedEmploymentPeriod:
    """Declared employment interval without inferred duration."""

    record_id: str
    employer: str | None
    start_date: str | None
    end_date: str | None
    provenance: ImportProvenance


@dataclass(frozen=True)
class ImportedClassification:
    """Declared classification interval."""

    record_id: str
    classification: str | None
    coefficient: str | None
    start_date: str | None
    end_date: str | None
    provenance: ImportProvenance


@dataclass(frozen=True)
class ImportedNightWork:
    """Declared night-work interval without computed duration."""

    record_id: str
    start_date: str | None
    end_date: str | None
    schedule: str | None
    provenance: ImportProvenance


@dataclass(frozen=True)
class ImportedFiveShift:
    """Declared five-shift interval without computed duration."""

    record_id: str
    start_date: str | None
    end_date: str | None
    schedule: str | None
    provenance: ImportProvenance


@dataclass(frozen=True)
class ImportedExposure:
    """Declared exposure metadata without medical or legal inference."""

    record_id: str
    exposure_type: str | None
    start_date: str | None
    end_date: str | None
    provenance: ImportProvenance


@dataclass(frozen=True)
class ImportedEvidence:
    """Minimal evidence metadata prepared for the existing EvidenceBundle."""

    evidence_id: str
    source_type: str
    status: str
    reference: str
    provenance: ImportProvenance

    @property
    def record_id(self) -> str:
        """Expose the evidence identifier to generic batch operations."""

        return self.evidence_id


ImportRecord = (
    ImportedCareerRecord
    | ImportedEmploymentPeriod
    | ImportedClassification
    | ImportedNightWork
    | ImportedFiveShift
    | ImportedExposure
    | ImportedEvidence
)


@dataclass(frozen=True)
class ImportBatch:
    """Immutable collection of injected document and record metadata."""

    batch_id: str
    documents: tuple[ImportDocument, ...] = ()
    records: tuple[ImportRecord, ...] = ()
    status: ImportStatus = ImportStatus.CREATED
    synthetic_only: bool = True


@dataclass(frozen=True)
class ImportIssue:
    """One structural validation issue requiring review."""

    issue_id: str
    issue_type: ImportIssueType
    record_ids: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class ImportWarning:
    """Non-blocking import warning."""

    warning_id: str
    description: str


@dataclass(frozen=True)
class ImportValidation:
    """Immutable validation result without automatic correction."""

    valid: bool
    issues: tuple[ImportIssue, ...]
    warnings: tuple[ImportWarning, ...] = ()


@dataclass(frozen=True)
class ImportNormalization:
    """Separate normalized projection preserving all original values."""

    record_id: str
    original_values: tuple[tuple[str, str | None], ...]
    normalized_values: tuple[tuple[str, str | None], ...]
    transformations: tuple[str, ...]
    provenance: ImportProvenance


@dataclass(frozen=True)
class ImportConflict:
    """Preserved contradiction between imported metadata records."""

    conflict_id: str
    conflict_type: ImportConflictType
    record_ids: tuple[str, ...]
    description: str
    provenance_ids: tuple[str, ...]


@dataclass(frozen=True)
class ImportRecommendation:
    """Prudent next step after structural import review."""

    recommendation_id: str
    action: str


@dataclass(frozen=True)
class ImportSummary:
    """Explainable summary of one in-memory import batch."""

    batch_id: str
    status: ImportStatus
    document_ids: tuple[str, ...]
    record_ids: tuple[str, ...]
    issue_ids: tuple[str, ...]
    conflict_ids: tuple[str, ...]
    normalized_record_ids: tuple[str, ...]


@dataclass(frozen=True)
class ImportReport:
    """Audience-safe import report without source document content."""

    view: ImportReportView
    summary: ImportSummary
    documents_received: tuple[str, ...]
    missing_documents: tuple[str, ...]
    inconsistencies: tuple[str, ...]
    next_steps: tuple[str, ...]
    warnings: tuple[str, ...]
    provenance: tuple[str, ...] = ()
    normalizations: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    validations: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
