"""Immutable models for a synthetic career timeline.

This module represents facts and documentary uncertainty only.  It performs
no payroll, pension, eligibility, duration or retirement calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CareerEventType(str, Enum):
    """Supported kinds of declarative career event."""

    COMPANY_ENTRY = "COMPANY_ENTRY"
    COMPANY_EXIT = "COMPANY_EXIT"
    TRANSFER = "TRANSFER"
    PROMOTION = "PROMOTION"
    JOB_CHANGE = "JOB_CHANGE"
    COEFFICIENT_CHANGE = "COEFFICIENT_CHANGE"
    CLASSIFICATION_CHANGE = "CLASSIFICATION_CHANGE"
    NIGHT_WORK = "NIGHT_WORK"
    FIVE_SHIFT = "FIVE_SHIFT"
    SHIFT_WORK = "SHIFT_WORK"
    PART_TIME = "PART_TIME"
    TRAINING = "TRAINING"
    ILLNESS = "ILLNESS"
    WORKPLACE_ACCIDENT = "WORKPLACE_ACCIDENT"
    OCCUPATIONAL_DISEASE = "OCCUPATIONAL_DISEASE"
    PARENTAL_LEAVE = "PARENTAL_LEAVE"
    MILITARY_SERVICE = "MILITARY_SERVICE"
    UNEMPLOYMENT = "UNEMPLOYMENT"
    RETURN_TO_WORK = "RETURN_TO_WORK"
    END_OF_CAREER = "END_OF_CAREER"
    RETIREMENT = "RETIREMENT"


class EvidenceLevel(str, Enum):
    """Declarative strength of an evidence reference."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    UNKNOWN = "UNKNOWN"


class TimelineConfidence(str, Enum):
    """Prudential confidence label; LOT 2 never computes a numeric score."""

    UNKNOWN = "UNKNOWN"
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class CareerEvidence:
    """Opaque reference to evidence without embedding document content."""

    evidence_id: str
    source: str
    evidence_level: EvidenceLevel
    reference: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class CareerEvent:
    """One dated career fact supplied by a declared source."""

    event_id: str
    start_date: str | None
    end_date: str | None
    event_type: CareerEventType
    description: str
    source: str
    evidence_level: EvidenceLevel
    comment: str | None = None


@dataclass(frozen=True)
class CareerPeriod:
    """Generic career interval linked to events and evidence."""

    period_id: str
    start_date: str | None
    end_date: str | None
    event_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Employer:
    """Non-nominative employer reference used to structure a timeline."""

    employer_id: str
    label: str
    source: str


@dataclass(frozen=True)
class JobPosition:
    """Declared job position, without classification inference."""

    position_id: str
    employer_id: str | None
    label: str
    start_date: str | None
    end_date: str | None


@dataclass(frozen=True)
class ClassificationHistory:
    """Declared coefficient or classification interval."""

    history_id: str
    classification: str
    coefficient: str | None
    start_date: str | None
    end_date: str | None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkSchedule:
    """Declared work schedule without derived working-time calculation."""

    schedule_id: str
    schedule_type: str
    start_date: str | None
    end_date: str | None
    description: str | None = None


@dataclass(frozen=True)
class NightWorkPeriod:
    """Declared night-work interval awaiting documentary confirmation."""

    period_id: str
    start_date: str | None
    end_date: str | None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class FiveShiftPeriod:
    """Declared five-shift or 5x8 interval."""

    period_id: str
    start_date: str | None
    end_date: str | None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExposurePeriod:
    """Declared occupational exposure interval without eligibility inference."""

    period_id: str
    exposure_type: str
    start_date: str | None
    end_date: str | None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class LeavePeriod:
    """Declared absence interval such as illness or parental leave."""

    period_id: str
    leave_type: str
    start_date: str | None
    end_date: str | None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class CareerGap:
    """Unexplained interval reported for later documentary review."""

    gap_id: str
    start_date: str | None
    end_date: str | None
    description: str


@dataclass(frozen=True)
class CareerConflict:
    """Contradiction between supplied career facts; never auto-resolved."""

    conflict_id: str
    conflict_type: str
    event_refs: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class CareerTimeline:
    """Immutable collection of synthetic career facts from explicit sources."""

    timeline_id: str
    employee_case_id: str | None = None
    events: tuple[CareerEvent, ...] = ()
    evidence: tuple[CareerEvidence, ...] = ()
    source_ids: tuple[str, ...] = ()
    synthetic_only: bool = True


@dataclass(frozen=True)
class TimelineReport:
    """Structural timeline report with uncertainty and no retirement estimate."""

    timeline: CareerTimeline
    events: tuple[CareerEvent, ...]
    uncertainty_zones: tuple[str, ...]
    evidence_used: tuple[CareerEvidence, ...]
    missing_evidence: tuple[str, ...]
    conflicts: tuple[CareerConflict, ...]
    global_confidence: TimelineConfidence = TimelineConfidence.UNKNOWN
