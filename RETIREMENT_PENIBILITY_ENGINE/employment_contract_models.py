"""Immutable metadata-only models for synthetic employment contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .career_import_models import ImportBatch
from .career_reconstruction_models import ReconstructionProposal


class EmploymentConfidence(str, Enum):
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EmploymentStatus(str, Enum):
    EMPTY = "EMPTY"
    DRAFT = "DRAFT"
    VALID = "VALID"
    INVALID = "INVALID"
    READY_FOR_IMPORT = "READY_FOR_IMPORT"


class EmploymentReportView(str, Enum):
    EMPLOYEE_VIEW = "EMPLOYEE_VIEW"
    EXPERT_VIEW = "EXPERT_VIEW"


@dataclass(frozen=True)
class EmploymentMetadata:
    """Synthetic contract provenance without personal identifiers or content."""

    contract_id: str
    source_reference: str
    imported_at: str
    version: str
    confidence: EmploymentConfidence
    synthetic_only: bool = True


@dataclass(frozen=True)
class EmploymentEmployer:
    employer_id: str
    label: str | None
    source_reference: str


@dataclass(frozen=True)
class EmploymentSite:
    site_id: str
    employer_id: str
    synthetic_label: str | None


@dataclass(frozen=True)
class EmploymentPeriod:
    period_id: str
    employer_id: str
    site_id: str | None
    start_date: str | None
    end_date: str | None


@dataclass(frozen=True)
class EmploymentPosition:
    position_id: str
    period_id: str
    label: str | None
    effective_date: str | None


@dataclass(frozen=True)
class EmploymentClassification:
    classification_id: str
    period_id: str
    label: str | None
    effective_date: str | None


@dataclass(frozen=True)
class EmploymentCoefficient:
    coefficient_id: str
    classification_id: str
    value: str | None
    effective_date: str | None


@dataclass(frozen=True)
class EmploymentSchedule:
    schedule_id: str
    period_id: str
    label: str | None
    effective_date: str | None


@dataclass(frozen=True)
class EmploymentWorkingTime:
    working_time_id: str
    schedule_id: str
    declared_hours: str | None
    unit: str = "HOURS"


@dataclass(frozen=True)
class EmploymentFiveShift:
    five_shift_id: str
    schedule_id: str
    declared: bool = True


@dataclass(frozen=True)
class EmploymentNightWork:
    night_work_id: str
    period_id: str
    declared: bool = True
    schedule_reference: str | None = None


@dataclass(frozen=True)
class EmploymentEvidence:
    evidence_id: str
    evidence_type: str
    opaque_reference: str


@dataclass(frozen=True)
class EmploymentAmendment:
    amendment_id: str
    version: str
    effective_date: str | None
    supersedes_version: str | None
    change_types: tuple[str, ...]
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class EmploymentContract:
    """Synthetic employment contract and amendment history."""

    metadata: EmploymentMetadata
    employer: EmploymentEmployer | None = None
    sites: tuple[EmploymentSite, ...] = ()
    periods: tuple[EmploymentPeriod, ...] = ()
    positions: tuple[EmploymentPosition, ...] = ()
    classifications: tuple[EmploymentClassification, ...] = ()
    coefficients: tuple[EmploymentCoefficient, ...] = ()
    schedules: tuple[EmploymentSchedule, ...] = ()
    working_times: tuple[EmploymentWorkingTime, ...] = ()
    five_shift: tuple[EmploymentFiveShift, ...] = ()
    night_work: tuple[EmploymentNightWork, ...] = ()
    amendments: tuple[EmploymentAmendment, ...] = ()
    evidence: tuple[EmploymentEvidence, ...] = ()
    status: EmploymentStatus = EmploymentStatus.DRAFT


@dataclass(frozen=True)
class EmploymentIssue:
    issue_id: str
    issue_type: str
    subject_ids: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class EmploymentWarning:
    warning_id: str
    description: str


@dataclass(frozen=True)
class EmploymentValidation:
    valid: bool
    status: EmploymentStatus
    issues: tuple[EmploymentIssue, ...] = ()
    warnings: tuple[EmploymentWarning, ...] = ()


@dataclass(frozen=True)
class EmploymentContractInformation:
    contract_id: str
    period_ids: tuple[str, ...]
    amendment_ids: tuple[str, ...]
    positions: tuple[str, ...]
    classifications: tuple[str, ...]
    coefficients: tuple[str, ...]
    schedules: tuple[str, ...]
    working_times: tuple[str, ...]
    five_shift_ids: tuple[str, ...]
    night_work_ids: tuple[str, ...]


@dataclass(frozen=True)
class EmploymentImport:
    contract_id: str
    import_batch: ImportBatch
    converted_record_ids: tuple[str, ...]
    reconstruction_proposal: ReconstructionProposal | None = None


@dataclass(frozen=True)
class EmploymentSummary:
    contract_id: str
    status: EmploymentStatus
    contracts: int
    amendments: int
    periods: int
    issues: int
    requires_human_review: bool = True


@dataclass(frozen=True)
class EmploymentReport:
    view: EmploymentReportView
    summary: EmploymentSummary
    detected_contracts: tuple[str, ...]
    detected_amendments: tuple[str, ...]
    recognized_periods: tuple[str, ...]
    missing_information: tuple[str, ...]
    next_steps: tuple[str, ...]
    provenance: tuple[str, ...] = ()
    classifications: tuple[str, ...] = ()
    coefficients: tuple[str, ...] = ()
    schedules: tuple[str, ...] = ()
    amendments: tuple[str, ...] = ()
    history: tuple[str, ...] = ()
    documentary_consistency: tuple[str, ...] = ()
    career_import_preparation: tuple[str, ...] = ()
