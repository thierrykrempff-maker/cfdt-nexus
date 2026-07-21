"""Immutable metadata-only models for synthetic Kelio exports."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .career_import_models import ImportBatch
from .career_reconstruction_models import ReconstructionProposal


class KelioConfidence(str, Enum):
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class KelioStatus(str, Enum):
    EMPTY = "EMPTY"
    DRAFT = "DRAFT"
    VALID = "VALID"
    INVALID = "INVALID"
    READY_FOR_IMPORT = "READY_FOR_IMPORT"


class KelioReportView(str, Enum):
    EMPLOYEE_VIEW = "EMPLOYEE_VIEW"
    EXPERT_VIEW = "EXPERT_VIEW"


@dataclass(frozen=True)
class KelioMetadata:
    export_id: str
    source_reference: str
    imported_at: str
    version: str
    confidence: KelioConfidence
    synthetic_only: bool = True


@dataclass(frozen=True)
class KelioEmployee:
    synthetic_employee_id: str
    anonymized: bool = True


@dataclass(frozen=True)
class KelioSchedule:
    schedule_id: str
    label: str | None
    effective_date: str | None


@dataclass(frozen=True)
class KelioWorkingDay:
    working_day_id: str
    date: str | None
    schedule_id: str


@dataclass(frozen=True)
class KelioShift:
    shift_id: str
    working_day_id: str
    start_at: str | None
    end_at: str | None


@dataclass(frozen=True)
class KelioNightWork:
    night_work_id: str
    shift_id: str
    declared_duration: str | None


@dataclass(frozen=True)
class KelioFiveShift:
    five_shift_id: str
    schedule_id: str
    start_date: str | None
    end_date: str | None
    declared: bool = True


@dataclass(frozen=True)
class KelioOnCall:
    on_call_id: str
    start_at: str | None
    end_at: str | None


@dataclass(frozen=True)
class KelioIntervention:
    intervention_id: str
    on_call_id: str
    start_at: str | None
    end_at: str | None


@dataclass(frozen=True)
class KelioLeave:
    leave_id: str
    leave_type: str | None
    start_date: str | None
    end_date: str | None


@dataclass(frozen=True)
class KelioWorkingTime:
    working_time_id: str
    start_date: str | None
    end_date: str | None
    declared_hours: str | None


@dataclass(frozen=True)
class KelioCounter:
    counter_id: str
    label: str | None
    declared_value: str | None
    observed_at: str | None


@dataclass(frozen=True)
class KelioEvidence:
    evidence_id: str
    evidence_type: str
    opaque_reference: str


@dataclass(frozen=True)
class KelioExport:
    """Complete in-memory synthetic export; no file content is represented."""

    metadata: KelioMetadata
    employee: KelioEmployee
    schedules: tuple[KelioSchedule, ...] = ()
    working_days: tuple[KelioWorkingDay, ...] = ()
    shifts: tuple[KelioShift, ...] = ()
    night_work: tuple[KelioNightWork, ...] = ()
    five_shift: tuple[KelioFiveShift, ...] = ()
    on_calls: tuple[KelioOnCall, ...] = ()
    interventions: tuple[KelioIntervention, ...] = ()
    leaves: tuple[KelioLeave, ...] = ()
    working_times: tuple[KelioWorkingTime, ...] = ()
    counters: tuple[KelioCounter, ...] = ()
    evidence: tuple[KelioEvidence, ...] = ()
    status: KelioStatus = KelioStatus.DRAFT


@dataclass(frozen=True)
class KelioIssue:
    issue_id: str
    issue_type: str
    subject_ids: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class KelioWarning:
    warning_id: str
    description: str


@dataclass(frozen=True)
class KelioValidation:
    valid: bool
    status: KelioStatus
    issues: tuple[KelioIssue, ...] = ()
    warnings: tuple[KelioWarning, ...] = ()


@dataclass(frozen=True)
class KelioWorkingTimeInformation:
    working_period_ids: tuple[str, ...]
    schedule_labels: tuple[str, ...]
    night_work_ids: tuple[str, ...]
    five_shift_ids: tuple[str, ...]
    on_call_ids: tuple[str, ...]
    intervention_ids: tuple[str, ...]
    leave_ids: tuple[str, ...]
    counters: tuple[str, ...]


@dataclass(frozen=True)
class KelioImport:
    export_id: str
    import_batch: ImportBatch
    converted_record_ids: tuple[str, ...]
    reconstruction_proposal: ReconstructionProposal | None = None


@dataclass(frozen=True)
class KelioSummary:
    export_id: str
    status: KelioStatus
    working_periods: int
    night_periods: int
    five_shift_periods: int
    issues: int
    requires_human_review: bool = True


@dataclass(frozen=True)
class KelioReport:
    view: KelioReportView
    summary: KelioSummary
    recognized_periods: tuple[str, ...]
    detected_night_work: tuple[str, ...]
    detected_five_shift: tuple[str, ...]
    absences: tuple[str, ...]
    points_to_verify: tuple[str, ...]
    provenance: tuple[str, ...] = ()
    schedules: tuple[str, ...] = ()
    counters: tuple[str, ...] = ()
    on_calls: tuple[str, ...] = ()
    documentary_consistency: tuple[str, ...] = ()
    career_import_preparation: tuple[str, ...] = ()
