"""Immutable metadata-only models for synthetic career statements."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .career_import_models import ImportBatch
from .career_reconstruction_models import ReconstructionProposal


class CareerStatementConfidence(str, Enum):
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CareerStatementSource(str, Enum):
    CARSAT = "CARSAT"
    CNAV = "CNAV"
    EMPLOYEE_PROVIDED = "EMPLOYEE_PROVIDED"
    SYNTHETIC_TEST = "SYNTHETIC_TEST"
    UNKNOWN = "UNKNOWN"


class CareerStatementStatus(str, Enum):
    EMPTY = "EMPTY"
    DRAFT = "DRAFT"
    VALID = "VALID"
    INVALID = "INVALID"
    READY_FOR_IMPORT = "READY_FOR_IMPORT"


class CareerStatementPrecision(str, Enum):
    EXACT = "EXACT"
    MONTH_ONLY = "MONTH_ONLY"
    YEAR_ONLY = "YEAR_ONLY"
    APPROXIMATE = "APPROXIMATE"
    UNKNOWN = "UNKNOWN"


class CareerStatementReportView(str, Enum):
    EMPLOYEE_VIEW = "EMPLOYEE_VIEW"
    EXPERT_VIEW = "EXPERT_VIEW"


@dataclass(frozen=True)
class CareerStatementMetadata:
    """Non-identifying metadata supplied with a synthetic statement."""

    statement_id: str
    source: CareerStatementSource
    source_reference: str
    issued_at: str | None
    imported_at: str
    version: str
    confidence: CareerStatementConfidence
    synthetic_only: bool = True


@dataclass(frozen=True)
class CareerStatementHeader:
    """Technical statement header excluding personal identifiers."""

    scheme: str | None = None
    generated_at: str | None = None
    period_count_declared: int | None = None
    language: str = "fr"


@dataclass(frozen=True)
class CareerStatementReference:
    """Opaque documentary reference; it never contains document content."""

    reference_id: str
    reference_type: str
    opaque_reference: str


@dataclass(frozen=True)
class CareerStatementEmployer:
    """Synthetic employer label used only to relate declared periods."""

    employer_id: str
    label: str | None
    source_reference: str


@dataclass(frozen=True)
class CareerStatementPeriod:
    """Declared career period with explicit, unaltered date precision."""

    period_id: str
    period_type: str
    start_date: str | None
    end_date: str | None
    start_precision: CareerStatementPrecision = CareerStatementPrecision.UNKNOWN
    end_precision: CareerStatementPrecision = CareerStatementPrecision.UNKNOWN
    description: str | None = None
    reference_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CareerStatementEmployment:
    """Declared employment relation without duration or pension inference."""

    employment_id: str
    employer_id: str
    start_date: str | None
    end_date: str | None
    start_precision: CareerStatementPrecision = CareerStatementPrecision.UNKNOWN
    end_precision: CareerStatementPrecision = CareerStatementPrecision.UNKNOWN
    reference_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CareerStatement:
    """Complete in-memory synthetic statement; original values are immutable."""

    metadata: CareerStatementMetadata
    header: CareerStatementHeader
    employers: tuple[CareerStatementEmployer, ...] = ()
    employments: tuple[CareerStatementEmployment, ...] = ()
    periods: tuple[CareerStatementPeriod, ...] = ()
    references: tuple[CareerStatementReference, ...] = ()
    status: CareerStatementStatus = CareerStatementStatus.DRAFT


@dataclass(frozen=True)
class CareerStatementWarning:
    warning_id: str
    description: str


@dataclass(frozen=True)
class CareerStatementIssue:
    issue_id: str
    issue_type: str
    subject_ids: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class CareerStatementConflict:
    conflict_id: str
    conflict_type: str
    subject_ids: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class CareerStatementValidation:
    valid: bool
    status: CareerStatementStatus
    issues: tuple[CareerStatementIssue, ...] = ()
    warnings: tuple[CareerStatementWarning, ...] = ()
    conflicts: tuple[CareerStatementConflict, ...] = ()


@dataclass(frozen=True)
class CareerStatementConversion:
    statement_id: str
    import_batch: ImportBatch
    converted_record_ids: tuple[str, ...]
    warnings: tuple[CareerStatementWarning, ...] = ()


@dataclass(frozen=True)
class CareerStatementImport:
    statement_id: str
    conversion: CareerStatementConversion
    reconstruction_proposal: ReconstructionProposal | None = None


@dataclass(frozen=True)
class CareerStatementSummary:
    statement_id: str
    status: CareerStatementStatus
    employers: int
    employments: int
    periods: int
    references: int
    issues: int
    requires_human_review: bool = True


@dataclass(frozen=True)
class CareerStatementReport:
    view: CareerStatementReportView
    summary: CareerStatementSummary
    imported_documents: tuple[str, ...]
    recognized_periods: tuple[str, ...]
    incomplete_periods: tuple[str, ...]
    points_to_verify: tuple[str, ...]
    next_steps: tuple[str, ...]
    metadata: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    consistency: tuple[str, ...] = ()
    quality: tuple[str, ...] = ()
    validation: tuple[str, ...] = ()
    import_preparation: tuple[str, ...] = ()
