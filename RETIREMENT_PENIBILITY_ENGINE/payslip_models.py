"""Immutable metadata-only models for synthetic payslips."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .career_import_models import ImportBatch
from .career_reconstruction_models import ReconstructionProposal


class PayslipConfidence(str, Enum):
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class PayslipStatus(str, Enum):
    EMPTY = "EMPTY"
    DRAFT = "DRAFT"
    VALID = "VALID"
    INVALID = "INVALID"
    READY_FOR_IMPORT = "READY_FOR_IMPORT"


class PayslipReportView(str, Enum):
    EMPLOYEE_VIEW = "EMPLOYEE_VIEW"
    EXPERT_VIEW = "EXPERT_VIEW"


@dataclass(frozen=True)
class PayslipMetadata:
    """Synthetic source metadata with no personal or banking identifier."""

    payslip_id: str
    source_reference: str
    imported_at: str
    version: str
    confidence: PayslipConfidence
    synthetic_only: bool = True


@dataclass(frozen=True)
class PayslipHeader:
    """Technical header describing the declared payroll period."""

    issue_date: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    currency: str = "EUR"


@dataclass(frozen=True)
class PayslipEmployee:
    """Anonymous synthetic employee reference only."""

    synthetic_employee_id: str
    anonymized: bool = True


@dataclass(frozen=True)
class PayslipEmployer:
    employer_id: str
    label: str | None
    source_reference: str


@dataclass(frozen=True)
class PayslipPeriod:
    period_id: str
    employer_id: str
    start_date: str | None
    end_date: str | None


@dataclass(frozen=True)
class PayslipWorkingTime:
    working_time_id: str
    period_id: str
    declared_hours: str | None
    schedule_label: str | None


@dataclass(frozen=True)
class PayslipNightWork:
    night_work_id: str
    period_id: str
    declared_hours: str | None
    declared: bool = True


@dataclass(frozen=True)
class PayslipFiveShift:
    five_shift_id: str
    period_id: str
    schedule_label: str | None
    declared: bool = True


@dataclass(frozen=True)
class PayslipClassification:
    classification_id: str
    period_id: str
    label: str | None


@dataclass(frozen=True)
class PayslipCoefficient:
    coefficient_id: str
    classification_id: str
    value: str | None


@dataclass(frozen=True)
class PayslipSalaryItem:
    item_id: str
    code: str | None
    label: str | None
    declared_amount: str | None = None


@dataclass(frozen=True)
class PayslipContribution:
    contribution_id: str
    code: str | None
    label: str | None
    declared_amount: str | None = None


@dataclass(frozen=True)
class PayslipAbsence:
    absence_id: str
    period_id: str
    absence_type: str | None
    declared_duration: str | None = None


@dataclass(frozen=True)
class PayslipOvertime:
    overtime_id: str
    period_id: str
    declared_hours: str | None
    rate_label: str | None = None


@dataclass(frozen=True)
class PayslipEvidence:
    evidence_id: str
    evidence_type: str
    opaque_reference: str


@dataclass(frozen=True)
class Payslip:
    """Complete immutable synthetic payslip metadata aggregate."""

    metadata: PayslipMetadata
    header: PayslipHeader
    employee: PayslipEmployee
    employer: PayslipEmployer | None = None
    periods: tuple[PayslipPeriod, ...] = ()
    working_times: tuple[PayslipWorkingTime, ...] = ()
    night_work: tuple[PayslipNightWork, ...] = ()
    five_shift: tuple[PayslipFiveShift, ...] = ()
    classifications: tuple[PayslipClassification, ...] = ()
    coefficients: tuple[PayslipCoefficient, ...] = ()
    salary_items: tuple[PayslipSalaryItem, ...] = ()
    contributions: tuple[PayslipContribution, ...] = ()
    absences: tuple[PayslipAbsence, ...] = ()
    overtime: tuple[PayslipOvertime, ...] = ()
    evidence: tuple[PayslipEvidence, ...] = ()
    status: PayslipStatus = PayslipStatus.DRAFT


@dataclass(frozen=True)
class PayslipIssue:
    issue_id: str
    issue_type: str
    subject_ids: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class PayslipWarning:
    warning_id: str
    description: str


@dataclass(frozen=True)
class PayslipValidation:
    valid: bool
    status: PayslipStatus
    issues: tuple[PayslipIssue, ...] = ()
    warnings: tuple[PayslipWarning, ...] = ()


@dataclass(frozen=True)
class PayslipPayrollInformation:
    period_ids: tuple[str, ...]
    classification_labels: tuple[str, ...]
    coefficient_values: tuple[str, ...]
    schedule_labels: tuple[str, ...]
    night_work_ids: tuple[str, ...]
    five_shift_ids: tuple[str, ...]
    salary_item_codes: tuple[str, ...]
    contribution_codes: tuple[str, ...]
    absence_types: tuple[str, ...]
    overtime_ids: tuple[str, ...]


@dataclass(frozen=True)
class PayslipImport:
    payslip_id: str
    import_batch: ImportBatch
    converted_record_ids: tuple[str, ...]
    reconstruction_proposal: ReconstructionProposal | None = None


@dataclass(frozen=True)
class PayslipSummary:
    payslip_id: str
    status: PayslipStatus
    periods: int
    payroll_items: int
    issues: int
    requires_human_review: bool = True


@dataclass(frozen=True)
class PayslipReport:
    view: PayslipReportView
    summary: PayslipSummary
    recognized_periods: tuple[str, ...]
    detected_information: tuple[str, ...]
    missing_information: tuple[str, ...]
    next_steps: tuple[str, ...]
    detected_items: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    classifications: tuple[str, ...] = ()
    schedules: tuple[str, ...] = ()
    night_work: tuple[str, ...] = ()
    five_shift: tuple[str, ...] = ()
    validation: tuple[str, ...] = ()
    career_import_preparation: tuple[str, ...] = ()
