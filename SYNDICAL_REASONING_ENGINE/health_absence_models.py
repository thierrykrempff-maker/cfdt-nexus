"""Immutable R1E contracts for health-related absence and social protection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import ConfidenceLevel, SyndicalReasoningReport, UrgencyLevel


class HealthSituation(str, Enum):
    ORDINARY_SICK_LEAVE = "ordinary_sick_leave"
    EXTENSION = "extension"
    LATE_TRANSMISSION = "late_transmission"
    POTENTIALLY_UNJUSTIFIED_ABSENCE = "potentially_unjustified_absence"
    REPORTED_WORK_ACCIDENT = "reported_work_accident"
    REPORTED_COMMUTING_ACCIDENT = "reported_commuting_accident"
    REPORTED_OCCUPATIONAL_DISEASE = "reported_occupational_disease"
    REPORTED_RELAPSE = "reported_relapse"
    CPAM_REVIEW = "cpam_review"
    EMPLOYER_RESERVATIONS = "employer_reservations"
    DAILY_ALLOWANCE = "daily_allowance"
    SUBROGATION = "subrogation"
    SALARY_MAINTENANCE = "salary_maintenance"
    WAITING_PERIOD = "waiting_period"
    EMPLOYER_SUPPLEMENT = "employer_supplement"
    PROVIDENT_COVER = "provident_cover"
    MUTUAL_INSURANCE = "mutual_insurance"
    PORTABILITY = "portability"
    RETURN_TO_WORK = "return_to_work"
    PRE_RETURN_VISIT = "pre_return_visit"
    RETURN_VISIT = "return_visit"
    THERAPEUTIC_PART_TIME = "therapeutic_part_time"
    WORK_ADJUSTMENT = "work_adjustment"
    DECLARED_RESTRICTION = "declared_restriction"
    REPORTED_UNFITNESS = "reported_unfitness"
    REDEPLOYMENT = "redeployment"
    FAMILY_LEAVE = "family_leave"
    LEAVE_COUNTER_IMPACT = "leave_counter_impact"
    SENIORITY_IMPACT = "seniority_impact"
    POTENTIAL_PAY_IMPACT = "potential_pay_impact"
    POSSIBLE_HEALTH_DISCRIMINATION = "possible_health_discrimination"


class CompetentActor(str, Enum):
    EMPLOYEE = "employee"
    EMPLOYER = "employer"
    HR = "human_resources"
    PAYROLL = "payroll_service"
    CPAM = "cpam"
    TREATING_DOCTOR = "treating_doctor"
    OCCUPATIONAL_PHYSICIAN = "occupational_physician"
    MEDICAL_ADVISER = "medical_adviser"
    LABOUR_INSPECTORATE = "labour_inspectorate"
    CSE = "cse"
    DISABILITY_OFFICER = "disability_officer"
    PROVIDENT_BODY = "provident_body"
    MUTUAL_INSURER = "mutual_insurer"
    INSURER = "insurer"
    AGIRC_ARRCO = "agirc_arrco"
    URSSAF = "urssaf"
    LEGAL_COUNSEL = "legal_counsel"
    UNION_REPRESENTATIVE = "union_representative"


class HealthHypothesis(str, Enum):
    JUSTIFIED_SICK_LEAVE = "justified_sick_leave_to_verify"
    TRANSMISSION_TO_VERIFY = "transmission_to_verify"
    POTENTIALLY_UNJUSTIFIED_ABSENCE = "potentially_unjustified_absence"
    RECOGNITION_PENDING = "occupational_recognition_pending"
    COMMUTING_ACCIDENT_POSSIBLE = "commuting_accident_possible"
    OCCUPATIONAL_DISEASE_PENDING = "occupational_disease_pending"
    SALARY_MAINTENANCE_POTENTIAL = "salary_maintenance_potential"
    SUBROGATION_TO_VERIFY = "subrogation_to_verify"
    DAILY_ALLOWANCE_POTENTIALLY_MISSING = "daily_allowance_potentially_missing"
    PAYROLL_TIMING_DIFFERENCE = "payroll_timing_difference_possible"
    PROVIDENT_COVER_POTENTIAL = "provident_cover_potential"
    RETURN_VISIT_POTENTIALLY_REQUIRED = "return_visit_potentially_required"
    ADJUSTMENT_TO_EXAMINE = "adjustment_to_examine"
    REDEPLOYMENT_TO_EXAMINE = "redeployment_to_examine"
    UNFITNESS_PROCEDURE_INCOMPLETE = "unfitness_procedure_potentially_incomplete"
    POSSIBLE_HEALTH_DISCRIMINATION = "possible_health_discrimination"
    POSSIBLE_ABSENCE_DISCIPLINE = "possible_absence_related_discipline"
    INSUFFICIENT_DATA = "insufficient_data"


class HealthEventKind(str, Enum):
    DECLARED_HEALTH_EVENT = "declared_health_event"
    INITIAL_LEAVE = "initial_leave"
    EXTENSION = "extension"
    EMPLOYER_TRANSMISSION = "employer_transmission"
    CPAM_TRANSMISSION = "cpam_transmission"
    ACCIDENT_REPORT = "accident_report"
    EMPLOYER_RESERVATIONS = "employer_reservations"
    CPAM_REVIEW = "cpam_review"
    CPAM_DECISION = "cpam_decision"
    DAILY_ALLOWANCE_PAYMENT = "daily_allowance_payment"
    SALARY_MAINTENANCE = "salary_maintenance"
    PAYROLL_ADJUSTMENT = "payroll_adjustment"
    PRE_RETURN_VISIT = "pre_return_visit"
    RETURN_VISIT = "return_visit"
    OCCUPATIONAL_HEALTH_OPINION = "occupational_health_opinion"
    WORK_ADJUSTMENT = "work_adjustment"
    REDEPLOYMENT_SEARCH = "redeployment_search"
    REDEPLOYMENT_PROPOSAL = "redeployment_proposal"
    RETURN_TO_WORK = "return_to_work"
    CONTRACT_TERMINATION = "contract_termination"
    PROVIDENT_REQUEST = "provident_request"
    INSURER_RESPONSE = "insurer_response"


class EventStatus(str, Enum):
    DECLARED = "declared"
    DOCUMENTED = "documented"
    PENDING = "pending"
    DECIDED = "decided"
    HYPOTHESIS = "hypothesis"


class QuestionPriority(str, Enum):
    CRITICAL = "critical"
    PRIORITY = "priority"
    USEFUL = "useful"
    COMPLEMENTARY = "complementary"


class EvidenceCategory(str, Enum):
    ESSENTIAL = "essential"
    USEFUL = "useful"
    COMPLEMENTARY = "complementary"


class UrgencyCategory(str, Enum):
    HUMAN = "human"
    MEDICAL = "medical"
    FINANCIAL = "financial"
    CONTRACTUAL = "contractual"
    ADMINISTRATIVE = "administrative"
    LITIGATION = "litigation"


@dataclass(frozen=True, slots=True)
class HealthTimelineEvent:
    event_id: str
    kind: HealthEventKind
    date_or_period: str | None
    date_certain: bool
    actor: CompetentActor
    associated_document_type: str | None
    status: EventStatus
    confidence: ConfidenceLevel
    potential_consequences: tuple[str, ...]
    next_known_deadline: str | None = None


@dataclass(frozen=True, slots=True)
class ActorResponsibility:
    actor: CompetentActor
    responsibilities: tuple[str, ...]
    prohibited_conclusions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class HealthQualification:
    hypothesis: HealthHypothesis
    supporting_facts: tuple[str, ...]
    weakening_facts: tuple[str, ...]
    missing_information: tuple[str, ...]
    sources_to_verify: tuple[str, ...]
    competent_actor: CompetentActor
    required_evidence: tuple[str, ...]
    alternative_explanations: tuple[str, ...]
    confidence: ConfidenceLevel
    urgency: UrgencyLevel
    possible_consequences: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HealthQuestion:
    priority: QuestionPriority
    question: str
    purpose: str


@dataclass(frozen=True, slots=True)
class HealthEvidence:
    evidence_type: str
    label: str
    category: EvidenceCategory
    utility: str
    can_demonstrate: str
    limitation: str
    confidentiality: str
    provider: CompetentActor


@dataclass(frozen=True, slots=True)
class HealthDocumentComparison:
    comparison_code: str
    left_document_type: str
    right_document_type: str
    concordances: tuple[str, ...]
    observed_gaps: tuple[str, ...]
    alternative_explanations: tuple[str, ...]
    missing_data: tuple[str, ...]
    reliability: ConfidenceLevel
    potential_impact: str
    actor_to_contact: CompetentActor
    calculation_performed: bool = False


@dataclass(frozen=True, slots=True)
class HealthPosition:
    arguments: tuple[str, ...]
    potential_rights_or_processes: tuple[str, ...]
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    available_evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    objections: tuple[str, ...]
    possible_responses: tuple[str, ...]
    undecidable_points: tuple[str, ...]
    decision_maker: CompetentActor


@dataclass(frozen=True, slots=True)
class HealthStrategy:
    level: int
    name: str
    objective: str
    urgency: UrgencyLevel
    actor: CompetentActor
    advantages: tuple[str, ...]
    limitations: tuple[str, ...]
    risks: tuple[str, ...]
    required_pieces: tuple[str, ...]
    expected_result: str
    next_step_if_unsuccessful: str


@dataclass(frozen=True, slots=True)
class HealthDomainArticulation:
    primary_domain: str
    complementary_domains: tuple[str, ...]
    rationale: str
    common_caution: str


@dataclass(frozen=True, slots=True)
class HealthAbsenceAnalysis:
    base_report: SyndicalReasoningReport
    situations: tuple[HealthSituation, ...]
    timeline: tuple[HealthTimelineEvent, ...]
    qualifications: tuple[HealthQualification, ...]
    actors: tuple[ActorResponsibility, ...]
    automatic_questions: tuple[HealthQuestion, ...]
    evidence: tuple[HealthEvidence, ...]
    comparisons: tuple[HealthDocumentComparison, ...]
    employee_position: HealthPosition
    employer_or_body_position: HealthPosition
    urgency_categories: tuple[UrgencyCategory, ...]
    strategies: tuple[HealthStrategy, ...]
    articulation: HealthDomainArticulation
    missing_information: tuple[str, ...]
    urgency: UrgencyLevel
    confidence: ConfidenceLevel
    scenario_code: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "analysis_type": "health_absence_social_protection",
            "situations": [item.value for item in self.situations],
            "timeline": [
                {
                    "event_id": item.event_id,
                    "kind": item.kind.value,
                    "date_or_period": item.date_or_period,
                    "date_certain": item.date_certain,
                    "actor": item.actor.value,
                    "associated_document_type": item.associated_document_type,
                    "status": item.status.value,
                    "confidence": item.confidence.value,
                    "potential_consequences": list(item.potential_consequences),
                    "next_known_deadline": item.next_known_deadline,
                }
                for item in self.timeline
            ],
            "qualifications": [
                {
                    "hypothesis": item.hypothesis.value,
                    "supporting_facts": list(item.supporting_facts),
                    "weakening_facts": list(item.weakening_facts),
                    "missing_information": list(item.missing_information),
                    "sources_to_verify": list(item.sources_to_verify),
                    "competent_actor": item.competent_actor.value,
                    "required_evidence": list(item.required_evidence),
                    "alternative_explanations": list(item.alternative_explanations),
                    "confidence": item.confidence.value,
                    "urgency": item.urgency.value,
                    "possible_consequences": list(item.possible_consequences),
                }
                for item in self.qualifications
            ],
            "actors": [
                {
                    "actor": item.actor.value,
                    "responsibilities": list(item.responsibilities),
                    "prohibited_conclusions": list(item.prohibited_conclusions),
                }
                for item in self.actors
            ],
            "automatic_questions": [
                {"priority": item.priority.value, "question": item.question, "purpose": item.purpose}
                for item in self.automatic_questions
            ],
            "evidence": [
                {
                    "evidence_type": item.evidence_type,
                    "label": item.label,
                    "category": item.category.value,
                    "utility": item.utility,
                    "can_demonstrate": item.can_demonstrate,
                    "limitation": item.limitation,
                    "confidentiality": item.confidentiality,
                    "provider": item.provider.value,
                }
                for item in self.evidence
            ],
            "comparisons": [
                {
                    "comparison_code": item.comparison_code,
                    "left_document_type": item.left_document_type,
                    "right_document_type": item.right_document_type,
                    "concordances": list(item.concordances),
                    "observed_gaps": list(item.observed_gaps),
                    "alternative_explanations": list(item.alternative_explanations),
                    "missing_data": list(item.missing_data),
                    "reliability": item.reliability.value,
                    "potential_impact": item.potential_impact,
                    "actor_to_contact": item.actor_to_contact.value,
                    "calculation_performed": item.calculation_performed,
                }
                for item in self.comparisons
            ],
            "employee_position": _position_dict(self.employee_position),
            "employer_or_body_position": _position_dict(self.employer_or_body_position),
            "urgency_categories": [item.value for item in self.urgency_categories],
            "strategies": [
                {
                    "level": item.level,
                    "name": item.name,
                    "objective": item.objective,
                    "urgency": item.urgency.value,
                    "actor": item.actor.value,
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
            "missing_information": list(self.missing_information),
            "urgency": self.urgency.value,
            "confidence": self.confidence.value,
            "scenario_code": self.scenario_code,
        }


def _position_dict(position: HealthPosition) -> dict[str, object]:
    return {
        "arguments": list(position.arguments),
        "potential_rights_or_processes": list(position.potential_rights_or_processes),
        "strengths": list(position.strengths),
        "weaknesses": list(position.weaknesses),
        "available_evidence": list(position.available_evidence),
        "missing_evidence": list(position.missing_evidence),
        "objections": list(position.objections),
        "possible_responses": list(position.possible_responses),
        "undecidable_points": list(position.undecidable_points),
        "decision_maker": position.decision_maker.value,
    }
