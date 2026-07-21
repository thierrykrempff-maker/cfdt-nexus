"""Immutable domain models for future retirement and penibility reasoning.

The models retain structured declarations and evidence references only. They
do not compute durations, points, eligibility, pensions or retirement dates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EvidenceGrade(str, Enum):
    """Documentary strength assigned by the declared evidence matrix."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"


class RetirementConfidence(str, Enum):
    """Prudential confidence reported without asserting legal certainty."""

    UNKNOWN = "UNKNOWN"
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RetirementOutputLevel(str, Enum):
    """Maximum wording level permitted by the available evidence."""

    INFORMATION_GENERALE = "INFORMATION_GENERALE"
    DROIT_POTENTIEL = "DROIT_POTENTIEL"
    DROIT_PROBABLE = "DROIT_PROBABLE"
    DROIT_CONFIRME_PAR_PIECE = "DROIT_CONFIRME_PAR_PIECE"
    A_FAIRE_VALIDER_PAR_CARSAT_OU_ASSURANCE_RETRAITE = (
        "A_FAIRE_VALIDER_PAR_CARSAT_OU_ASSURANCE_RETRAITE"
    )


@dataclass(frozen=True)
class CareerPeriod:
    """One declared career interval, without inferred duration or quarters."""

    period_id: str
    start_date: str | None
    end_date: str | None
    employer_reference: str | None = None
    activity_type: str | None = None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class NightWorkPeriod:
    """Declared night-work interval awaiting documentary confirmation."""

    period_id: str
    career_period_id: str | None
    start_date: str | None
    end_date: str | None
    schedule_description: str | None = None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class FiveShiftPeriod:
    """Declared five-shift or 5x8 interval, with no exposure inference."""

    period_id: str
    career_period_id: str | None
    start_date: str | None
    end_date: str | None
    organization_label: str = "5x8"
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExposurePeriod:
    """Declared occupational exposure and the references supporting it."""

    period_id: str
    exposure_factor: str
    start_date: str | None
    end_date: str | None
    declared_by: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class C2PInformation:
    """C2P information as declared or evidenced, never recomputed locally."""

    account_status: str
    declared_points: int | None = None
    statement_date: str | None = None
    evidence_refs: tuple[str, ...] = ()
    administrative_confirmation_required: bool = True


@dataclass(frozen=True)
class EmployeeCareer:
    """Opaque employee case containing isolated, explicitly supplied history."""

    career_id: str
    generation_year: int | None = None
    regime_hints: tuple[str, ...] = ()
    career_periods: tuple[CareerPeriod, ...] = ()
    night_work_periods: tuple[NightWorkPeriod, ...] = ()
    five_shift_periods: tuple[FiveShiftPeriod, ...] = ()
    exposure_periods: tuple[ExposurePeriod, ...] = ()
    c2p_information: C2PInformation | None = None
    synthetic_only: bool = True


@dataclass(frozen=True)
class EvidenceItem:
    """Reference to one available item; document content is not embedded."""

    evidence_id: str
    source_id: str
    document_type: str
    grade: EvidenceGrade
    reference: str | None = None
    effective_on: str | None = None
    verified: bool = False
    official: bool = False


@dataclass(frozen=True)
class MissingInformation:
    """Information or evidence still required before a stronger conclusion."""

    missing_id: str
    description: str
    reason: str
    blocking: bool
    requested_source: str | None = None


@dataclass(frozen=True)
class RetirementScenario:
    """Named hypothesis only; it contains no computed date or simulation."""

    scenario_id: str
    label: str
    assumptions: tuple[str, ...] = ()
    required_evidence_refs: tuple[str, ...] = ()
    applicable: bool | None = None
    output_level: RetirementOutputLevel = RetirementOutputLevel.INFORMATION_GENERALE


@dataclass(frozen=True)
class RetirementReport:
    """Prudent architecture-level report composed without retirement calculation."""

    report_id: str
    request_id: str
    summary: str
    scenarios: tuple[RetirementScenario, ...] = ()
    evidence_used: tuple[EvidenceItem, ...] = ()
    missing_information: tuple[MissingInformation, ...] = ()
    confidence: RetirementConfidence = RetirementConfidence.UNKNOWN
    output_level: RetirementOutputLevel = RetirementOutputLevel.INFORMATION_GENERALE
    recommended_actions: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
