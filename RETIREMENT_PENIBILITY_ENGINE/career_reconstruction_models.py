"""Immutable models for cautious, human-validated career reconstruction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .career_evidence_models import EvidenceBundle
from .career_import_models import ImportBatch, ImportProvenance
from .career_timeline_models import CareerTimeline


class ReconstructionStatus(str, Enum):
    PROPOSED = "PROPOSED"
    MATCHED = "MATCHED"
    MERGED = "MERGED"
    PARTIALLY_MERGED = "PARTIALLY_MERGED"
    CONFLICTED = "CONFLICTED"
    AMBIGUOUS = "AMBIGUOUS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    REQUIRES_HUMAN_VALIDATION = "REQUIRES_HUMAN_VALIDATION"
    REJECTED = "REJECTED"
    VALIDATED = "VALIDATED"


class ReconstructionMatchType(str, Enum):
    SAME_EMPLOYER = "SAME_EMPLOYER"
    SAME_PERIOD = "SAME_PERIOD"
    OVERLAPPING_PERIOD = "OVERLAPPING_PERIOD"
    ADJACENT_PERIOD = "ADJACENT_PERIOD"
    SAME_POSITION = "SAME_POSITION"
    SAME_CLASSIFICATION = "SAME_CLASSIFICATION"
    SAME_SCHEDULE = "SAME_SCHEDULE"
    SAME_SOURCE_REFERENCE = "SAME_SOURCE_REFERENCE"
    CORROBORATING_SOURCE = "CORROBORATING_SOURCE"
    CONTRADICTORY_SOURCE = "CONTRADICTORY_SOURCE"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    NO_MATCH = "NO_MATCH"


class ReconstructionConflictType(str, Enum):
    DATE_CONFLICT = "DATE_CONFLICT"
    EMPLOYER_CONFLICT = "EMPLOYER_CONFLICT"
    POSITION_CONFLICT = "POSITION_CONFLICT"
    CLASSIFICATION_CONFLICT = "CLASSIFICATION_CONFLICT"
    COEFFICIENT_CONFLICT = "COEFFICIENT_CONFLICT"
    SCHEDULE_CONFLICT = "SCHEDULE_CONFLICT"
    NIGHT_WORK_CONFLICT = "NIGHT_WORK_CONFLICT"
    FIVE_SHIFT_CONFLICT = "FIVE_SHIFT_CONFLICT"
    EXPOSURE_CONFLICT = "EXPOSURE_CONFLICT"
    SOURCE_VERSION_CONFLICT = "SOURCE_VERSION_CONFLICT"
    DUPLICATE_CONFLICT = "DUPLICATE_CONFLICT"
    PROVENANCE_CONFLICT = "PROVENANCE_CONFLICT"


class ReconstructionConfidence(str, Enum):
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DatePrecision(str, Enum):
    EXACT = "EXACT"
    MONTH_ONLY = "MONTH_ONLY"
    YEAR_ONLY = "YEAR_ONLY"
    APPROXIMATE = "APPROXIMATE"
    UNKNOWN = "UNKNOWN"


class ReconstructionReportView(str, Enum):
    EMPLOYEE_VIEW = "EMPLOYEE_VIEW"
    EXPERT_VIEW = "EXPERT_VIEW"


@dataclass(frozen=True)
class ReconstructionDate:
    value: str | None
    precision: DatePrecision
    earliest_possible: str | None = None
    latest_possible: str | None = None


ReconstructionValue = str | bool | ReconstructionDate | None


@dataclass(frozen=True)
class ReconstructionRequest:
    request_id: str
    question: str
    synthetic_only: bool = True


@dataclass(frozen=True)
class ReconstructionContext:
    context_id: str
    request: ReconstructionRequest
    import_batches: tuple[ImportBatch, ...] = ()
    existing_timeline: CareerTimeline | None = None
    existing_evidence: EvidenceBundle | None = None


@dataclass(frozen=True)
class ReconstructionRecord:
    record_id: str
    record_type: str
    values: tuple[tuple[str, ReconstructionValue], ...]
    original_record: object
    provenance: tuple[ImportProvenance, ...]


@dataclass(frozen=True)
class ReconstructionCandidate:
    candidate_id: str
    left_record_id: str
    right_record_id: str


@dataclass(frozen=True)
class ReconstructionMatch:
    match_id: str
    record_ids: tuple[str, str]
    matching_criteria: tuple[str, ...]
    divergent_criteria: tuple[str, ...]
    unknown_criteria: tuple[str, ...]
    match_type: ReconstructionMatchType
    confidence: ReconstructionConfidence
    justification: str


@dataclass(frozen=True)
class ReconstructionConflict:
    conflict_id: str
    conflict_type: ReconstructionConflictType
    record_ids: tuple[str, ...]
    alternative_values: tuple[tuple[str, tuple[ReconstructionValue, ...]], ...]
    provenance: tuple[ImportProvenance, ...]
    description: str


@dataclass(frozen=True)
class ReconstructionMerge:
    merge_id: str
    source_record_ids: tuple[str, ...]
    merged_values: tuple[tuple[str, ReconstructionValue], ...]
    alternative_values: tuple[tuple[str, tuple[ReconstructionValue, ...]], ...]
    provenance: tuple[ImportProvenance, ...]
    status: ReconstructionStatus


@dataclass(frozen=True)
class ReconstructedCareerPeriod:
    proposal_id: str
    employer: str | None
    start_date: ReconstructionDate
    end_date: ReconstructionDate
    provenance: tuple[ImportProvenance, ...]


@dataclass(frozen=True)
class ReconstructedCareerEvent:
    proposal_id: str
    event_type: str
    start_date: ReconstructionDate
    end_date: ReconstructionDate
    description: str
    provenance: tuple[ImportProvenance, ...]


@dataclass(frozen=True)
class ReconstructedClassification:
    proposal_id: str
    classification: str | None
    coefficient: str | None
    period: ReconstructedCareerPeriod


@dataclass(frozen=True)
class ReconstructedWorkSchedule:
    proposal_id: str
    schedule: str | None
    period: ReconstructedCareerPeriod


@dataclass(frozen=True)
class ReconstructedNightWorkPeriod:
    proposal_id: str
    period: ReconstructedCareerPeriod
    confirmed: bool = False


@dataclass(frozen=True)
class ReconstructedFiveShiftPeriod:
    proposal_id: str
    period: ReconstructedCareerPeriod
    confirmed: bool = False


@dataclass(frozen=True)
class ReconstructedExposurePeriod:
    proposal_id: str
    exposure_type: str | None
    period: ReconstructedCareerPeriod
    confirmed: bool = False


@dataclass(frozen=True)
class ReconstructionGap:
    gap_id: str
    gap_type: str
    record_ids: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class ReconstructionWarning:
    warning_id: str
    description: str


@dataclass(frozen=True)
class ReconstructionDecision:
    decision_id: str
    subject_id: str
    question: str
    decided: bool = False


@dataclass(frozen=True)
class HumanValidationRequirement:
    requirement_id: str
    reason: str
    decision_ids: tuple[str, ...]
    completed: bool = False


@dataclass(frozen=True)
class ReconstructionProposal:
    proposal_id: str
    status: ReconstructionStatus
    records: tuple[ReconstructionRecord, ...]
    matches: tuple[ReconstructionMatch, ...]
    merges: tuple[ReconstructionMerge, ...]
    proposed_events: tuple[ReconstructedCareerEvent, ...]
    proposed_periods: tuple[ReconstructedCareerPeriod, ...]
    proposed_evidence: EvidenceBundle
    conflicts: tuple[ReconstructionConflict, ...]
    gaps: tuple[ReconstructionGap, ...]
    human_decisions: tuple[ReconstructionDecision, ...]
    validation_requirement: HumanValidationRequirement


@dataclass(frozen=True)
class ReconstructionSummary:
    proposal_id: str
    status: ReconstructionStatus
    proposed_period_ids: tuple[str, ...]
    proposed_event_ids: tuple[str, ...]
    conflict_ids: tuple[str, ...]
    gap_ids: tuple[str, ...]
    human_validation_required: bool


@dataclass(frozen=True)
class ReconstructionReport:
    view: ReconstructionReportView
    summary: ReconstructionSummary
    proposed_periods: tuple[str, ...]
    recognized_information: tuple[str, ...]
    uncertain_information: tuple[str, ...]
    contradictions: tuple[str, ...]
    missing_documents: tuple[str, ...]
    questions_to_confirm: tuple[str, ...]
    next_steps: tuple[str, ...]
    warnings: tuple[str, ...]
    imported_sources: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    matches: tuple[str, ...] = ()
    proposed_merges: tuple[str, ...] = ()
    confidence_levels: tuple[str, ...] = ()
    timeline_proposal: tuple[str, ...] = ()
    evidence_proposal: tuple[str, ...] = ()
