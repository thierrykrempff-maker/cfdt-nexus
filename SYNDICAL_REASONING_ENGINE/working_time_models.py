"""Immutable contracts for working-time reasoning R1C."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import ConfidenceLevel, SyndicalReasoningReport, UrgencyLevel


class WorkingTimeSituation(str, Enum):
    EFFECTIVE_WORK = "effective_work"
    BREAK = "break"
    INTERRUPTED_BREAK = "interrupted_break"
    DRESSING_TIME = "dressing_time"
    SHOWER_TIME = "shower_time"
    BUSINESS_TRAVEL = "business_travel"
    COMMUTE = "commute"
    ON_CALL = "on_call"
    ON_CALL_INTERVENTION = "on_call_intervention"
    INTERVENTION_TRAVEL = "intervention_travel"
    NIGHT_WORK = "night_work"
    OCCASIONAL_NIGHT_HOURS = "occasional_night_hours"
    SHIFT_WORK = "shift_work"
    SUCCESSIVE_TEAMS = "successive_teams"
    FIVE_SHIFT = "five_shift"
    SUNDAY_WORK = "sunday_work"
    PUBLIC_HOLIDAY = "public_holiday"
    OVERTIME = "overtime"
    ADDITIONAL_HOURS = "additional_hours"
    SCHEDULE_OVERRUN = "schedule_overrun"
    ANNUALIZATION = "annualization"
    MODULATION = "modulation"
    WORK_CYCLE = "work_cycle"
    DAILY_REST = "daily_rest"
    WEEKLY_REST = "weekly_rest"
    COMPENSATORY_REST = "compensatory_rest"
    INFORMAL_RECOVERY = "informal_recovery"
    RTT = "rtt"
    PAID_LEAVE = "paid_leave"
    RECALL_DURING_REST = "recall_during_rest"
    OFF_HOURS_TRAINING = "off_hours_training"
    REPRESENTATIVE_MEETING_ON_REST = "representative_meeting_on_rest"
    POTENTIAL_PAY_IMPACT = "potential_pay_impact"


class ScheduleKind(str, Enum):
    THEORETICAL = "theoretical"
    DECLARED = "declared"
    OBSERVED = "observed"


class QuestionPriority(str, Enum):
    CRITICAL = "critical"
    PRIORITY = "priority"
    USEFUL = "useful"
    COMPLEMENTARY = "complementary"


class PayImpactLikelihood(str, Enum):
    CERTAIN_FROM_DATA = "certain_from_data"
    PROBABLE = "probable"
    POSSIBLE = "possible"
    NOT_DEMONSTRATED = "not_demonstrated"
    IMPOSSIBLE_WITHOUT_DATA = "impossible_without_additional_data"


class EvidenceCategory(str, Enum):
    ESSENTIAL = "essential"
    USEFUL = "useful"
    COMPLEMENTARY = "complementary"


@dataclass(frozen=True, slots=True)
class WorkingOrganization:
    regime: str | None = None
    cycle: str | None = None
    shift_based: bool | None = None
    five_shift: bool | None = None
    annualized: bool | None = None


@dataclass(frozen=True, slots=True)
class ScheduleObservation:
    kind: ScheduleKind
    description: str
    source_piece_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OnCallObservation:
    planned: bool | None
    intervention_reported: bool | None
    intervention_duration_known: bool
    travel_duration_known: bool


@dataclass(frozen=True, slots=True)
class RestObservation:
    rest_type: WorkingTimeSituation
    interruption_reported: bool | None
    duration_known: bool


@dataclass(frozen=True, slots=True)
class BreakObservation:
    interrupted: bool | None
    free_to_attend_personal_matters: bool | None
    required_to_remain_available: bool | None


@dataclass(frozen=True, slots=True)
class WorkingTimeQualification:
    qualification: WorkingTimeSituation
    supporting_facts: tuple[str, ...]
    weakening_facts: tuple[str, ...]
    missing_information: tuple[str, ...]
    sources_to_verify: tuple[str, ...]
    confidence: ConfidenceLevel
    possible_consequences: tuple[str, ...]
    urgency: UrgencyLevel


@dataclass(frozen=True, slots=True)
class WorkingTimeQuestion:
    priority: QuestionPriority
    question: str
    purpose: str


@dataclass(frozen=True, slots=True)
class WorkingTimeEvidence:
    document_type: str
    label: str
    category: EvidenceCategory
    utility: str
    can_demonstrate: str
    cannot_demonstrate_alone: str


@dataclass(frozen=True, slots=True)
class DocumentComparison:
    comparison_code: str
    left_document_type: str
    right_document_type: str
    matching_elements: tuple[str, ...]
    observed_differences: tuple[str, ...]
    alternative_explanations: tuple[str, ...]
    additional_pieces: tuple[str, ...]
    reliability: ConfidenceLevel
    potential_impact: str


@dataclass(frozen=True, slots=True)
class PotentialPayImpact:
    impact_type: str
    likelihood: PayImpactLikelihood
    rationale: str
    required_data: tuple[str, ...]
    calculation_performed: bool = False


@dataclass(frozen=True, slots=True)
class WorkingTimePosition:
    arguments: tuple[str, ...]
    observed_inconsistencies: tuple[str, ...]
    potential_rights_or_mechanisms: tuple[str, ...]
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    available_evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    risks_or_objections: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkingTimeStrategy:
    level: int
    name: str
    objective: str
    urgency: UrgencyLevel
    advantages: tuple[str, ...]
    limitations: tuple[str, ...]
    risks: tuple[str, ...]
    required_pieces: tuple[str, ...]
    expected_result: str
    next_step_if_unsuccessful: str


@dataclass(frozen=True, slots=True)
class DomainArticulation:
    primary_domain: str
    complementary_domains: tuple[str, ...]
    rationale: str
    common_caution: str


@dataclass(frozen=True, slots=True)
class WorkingTimeAnalysis:
    base_report: SyndicalReasoningReport
    situations: tuple[WorkingTimeSituation, ...]
    organization: WorkingOrganization
    schedules: tuple[ScheduleObservation, ...]
    on_call: OnCallObservation | None
    rests: tuple[RestObservation, ...]
    breaks: tuple[BreakObservation, ...]
    qualifications: tuple[WorkingTimeQualification, ...]
    automatic_questions: tuple[WorkingTimeQuestion, ...]
    evidence: tuple[WorkingTimeEvidence, ...]
    comparisons: tuple[DocumentComparison, ...]
    employee_position: WorkingTimePosition
    employer_position: WorkingTimePosition
    potential_pay_impacts: tuple[PotentialPayImpact, ...]
    strategies: tuple[WorkingTimeStrategy, ...]
    articulation: DomainArticulation
    available_source_ids: tuple[str, ...]
    missing_information: tuple[str, ...]
    urgency: UrgencyLevel
    confidence: ConfidenceLevel
    scenario_code: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "analysis_type": "working_time",
            "situations": [item.value for item in self.situations],
            "organization": {
                "regime": self.organization.regime,
                "cycle": self.organization.cycle,
                "shift_based": self.organization.shift_based,
                "five_shift": self.organization.five_shift,
                "annualized": self.organization.annualized,
            },
            "schedules": [
                {
                    "kind": item.kind.value,
                    "description": item.description,
                    "source_piece_ids": list(item.source_piece_ids),
                }
                for item in self.schedules
            ],
            "qualifications": [
                {
                    "qualification": item.qualification.value,
                    "supporting_facts": list(item.supporting_facts),
                    "weakening_facts": list(item.weakening_facts),
                    "missing_information": list(item.missing_information),
                    "sources_to_verify": list(item.sources_to_verify),
                    "confidence": item.confidence.value,
                    "possible_consequences": list(item.possible_consequences),
                    "urgency": item.urgency.value,
                }
                for item in self.qualifications
            ],
            "automatic_questions": [
                {
                    "priority": item.priority.value,
                    "question": item.question,
                    "purpose": item.purpose,
                }
                for item in self.automatic_questions
            ],
            "evidence": [
                {
                    "document_type": item.document_type,
                    "label": item.label,
                    "category": item.category.value,
                    "utility": item.utility,
                    "can_demonstrate": item.can_demonstrate,
                    "cannot_demonstrate_alone": item.cannot_demonstrate_alone,
                }
                for item in self.evidence
            ],
            "comparisons": [
                {
                    "comparison_code": item.comparison_code,
                    "left_document_type": item.left_document_type,
                    "right_document_type": item.right_document_type,
                    "matching_elements": list(item.matching_elements),
                    "observed_differences": list(item.observed_differences),
                    "alternative_explanations": list(item.alternative_explanations),
                    "additional_pieces": list(item.additional_pieces),
                    "reliability": item.reliability.value,
                    "potential_impact": item.potential_impact,
                }
                for item in self.comparisons
            ],
            "employee_position": _position_dict(self.employee_position),
            "employer_position": _position_dict(self.employer_position),
            "potential_pay_impacts": [
                {
                    "impact_type": item.impact_type,
                    "likelihood": item.likelihood.value,
                    "rationale": item.rationale,
                    "required_data": list(item.required_data),
                    "calculation_performed": item.calculation_performed,
                }
                for item in self.potential_pay_impacts
            ],
            "strategies": [
                {
                    "level": item.level,
                    "name": item.name,
                    "objective": item.objective,
                    "urgency": item.urgency.value,
                    "advantages": list(item.advantages),
                    "limitations": list(item.limitations),
                    "risks": list(item.risks),
                    "required_pieces": list(item.required_pieces),
                    "expected_result": item.expected_result,
                    "next_step_if_unsuccessful": item.next_step_if_unsuccessful,
                }
                for item in self.strategies
            ],
            "articulation": {
                "primary_domain": self.articulation.primary_domain,
                "complementary_domains": list(self.articulation.complementary_domains),
                "rationale": self.articulation.rationale,
                "common_caution": self.articulation.common_caution,
            },
            "available_source_ids": list(self.available_source_ids),
            "missing_information": list(self.missing_information),
            "urgency": self.urgency.value,
            "confidence": self.confidence.value,
            "scenario_code": self.scenario_code,
        }


def _position_dict(position: WorkingTimePosition) -> dict[str, object]:
    return {
        "arguments": list(position.arguments),
        "observed_inconsistencies": list(position.observed_inconsistencies),
        "potential_rights_or_mechanisms": list(position.potential_rights_or_mechanisms),
        "strengths": list(position.strengths),
        "weaknesses": list(position.weaknesses),
        "available_evidence": list(position.available_evidence),
        "missing_evidence": list(position.missing_evidence),
        "risks_or_objections": list(position.risks_or_objections),
    }
