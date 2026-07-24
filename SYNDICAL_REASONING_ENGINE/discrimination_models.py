"""Immutable R1D contracts for discrimination, harassment and equal treatment."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import ConfidenceLevel, SyndicalReasoningReport, UrgencyLevel


class SituationType(str, Enum):
    PROFESSIONAL_CONFLICT = "professional_conflict"
    MANAGEMENT_DYSFUNCTION = "management_dysfunction"
    ISOLATED_INAPPROPRIATE_BEHAVIOUR = "isolated_inappropriate_behaviour"
    POSSIBLE_MORAL_HARASSMENT = "possible_moral_harassment"
    POSSIBLE_SEXUAL_HARASSMENT = "possible_sexual_harassment"
    SEXIST_BEHAVIOUR = "sexist_behaviour"
    DIFFERENCE_IN_TREATMENT = "difference_in_treatment"
    POSSIBLE_DISCRIMINATION = "possible_discrimination"
    POSSIBLE_RETALIATION = "possible_retaliation"
    POSSIBLE_UNION_RIGHTS_INTERFERENCE = "possible_union_rights_interference"
    INSUFFICIENT_FACTS = "insufficient_facts"
    PROTECTION_URGENCY = "protection_urgency"


class ProtectedCriterion(str, Enum):
    SEX = "sex"
    PREGNANCY = "pregnancy"
    FAMILY_SITUATION = "family_situation"
    ORIGIN = "origin"
    AGE = "age"
    DISABILITY = "disability"
    HEALTH = "health"
    UNION_ACTIVITY = "union_activity"
    OPINIONS = "opinions"
    BELIEFS = "beliefs"
    SEXUAL_ORIENTATION = "sexual_orientation"
    GENDER_IDENTITY = "gender_identity"
    PLACE_OF_RESIDENCE = "place_of_residence"
    PHYSICAL_APPEARANCE = "physical_appearance"
    ECONOMIC_VULNERABILITY = "economic_vulnerability"
    REPRESENTATIVE_MANDATE = "representative_mandate"
    REPORTING_OR_TESTIMONY = "reporting_or_testimony"


class AdverseMeasure(str, Enum):
    SANCTION = "sanction"
    PROMOTION_REFUSAL = "promotion_refusal"
    CAREER_SLOWDOWN = "career_slowdown"
    JOB_CHANGE = "job_change"
    DUTY_REMOVAL = "duty_removal"
    BONUS_REDUCTION = "bonus_reduction"
    LOWER_PAY = "lower_pay"
    TRAINING_REFUSAL = "training_refusal"
    UNFAVOURABLE_SCHEDULE = "unfavourable_schedule"
    ISOLATION = "isolation"
    DISMISSAL = "dismissal"
    TRANSFER = "transfer"
    NEGATIVE_APPRAISAL = "negative_appraisal"
    NO_PAY_RISE = "no_pay_rise"
    HARSHER_DISCIPLINE = "harsher_discipline"


class TimelineEventKind(str, Enum):
    FACT = "fact"
    REPEATED_FACT = "repeated_fact"
    CONTINUOUS_PERIOD = "continuous_period"
    REPORT = "report"
    EMPLOYER_RESPONSE = "employer_response"
    LATER_MEASURE = "later_measure"
    DECLARED_SICK_LEAVE = "declared_sick_leave"
    JOB_CHANGE = "job_change"
    DUTY_REMOVAL = "duty_removal"
    APPRAISAL_DEGRADATION = "appraisal_degradation"
    BONUS_LOSS = "bonus_loss"
    TRAINING_REFUSAL = "training_refusal"
    WITNESS_EVENT = "witness_event"


class TemporalPrecision(str, Enum):
    CERTAIN = "certain"
    APPROXIMATE = "approximate"
    UNKNOWN = "unknown"


class StatementNature(str, Enum):
    FACT = "fact"
    INTERPRETATION = "interpretation"
    FEELING = "feeling"
    HYPOTHESIS = "hypothesis"
    ESTABLISHED = "established"


class QuestionPriority(str, Enum):
    CRITICAL = "critical"
    PRIORITY = "priority"
    USEFUL = "useful"
    COMPLEMENTARY = "complementary"


class EvidenceCategory(str, Enum):
    ESSENTIAL = "essential"
    USEFUL = "useful"
    COMPLEMENTARY = "complementary"


@dataclass(frozen=True, slots=True)
class TimelineEvent:
    event_id: str
    kind: TimelineEventKind
    period: str | None
    precision: TemporalPrecision
    factual_description: str
    nature: StatementNature
    source: str
    people_present: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    related_event_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ComparatorAssessment:
    comparator_type: str
    relevance: str
    similarities: tuple[str, ...]
    objective_differences: tuple[str, ...]
    missing_data: tuple[str, ...]
    reliability: ConfidenceLevel
    limitations: tuple[str, ...]
    alternative_explanations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QualificationHypothesis:
    situation: SituationType
    supporting_facts: tuple[str, ...]
    weakening_facts: tuple[str, ...]
    missing_elements: tuple[str, ...]
    legal_criteria_to_check: tuple[str, ...]
    required_evidence: tuple[str, ...]
    alternative_explanations: tuple[str, ...]
    confidence: ConfidenceLevel
    urgency: UrgencyLevel
    possible_consequences: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PrioritizedQuestion:
    priority: QuestionPriority
    question: str
    purpose: str


@dataclass(frozen=True, slots=True)
class EvidenceRequirement:
    evidence_type: str
    label: str
    category: EvidenceCategory
    utility: str
    can_demonstrate: str
    cannot_demonstrate_alone: str
    reliability: ConfidenceLevel
    acquisition_risk: str


@dataclass(frozen=True, slots=True)
class ContradictoryPosition:
    arguments: tuple[str, ...]
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    foreseeable_objections: tuple[str, ...]
    possible_responses: tuple[str, ...]
    unresolved_points: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProtectionStrategy:
    level: int
    name: str
    objective: str
    urgency: UrgencyLevel
    advantages: tuple[str, ...]
    limitations: tuple[str, ...]
    risks: tuple[str, ...]
    required_pieces: tuple[str, ...]
    competent_actor: str
    expected_result: str
    next_step_if_unsuccessful: str


@dataclass(frozen=True, slots=True)
class DomainArticulation:
    primary_domain: str
    complementary_domains: tuple[str, ...]
    rationale: str
    common_caution: str


@dataclass(frozen=True, slots=True)
class DiscriminationHarassmentAnalysis:
    base_report: SyndicalReasoningReport
    timeline: tuple[TimelineEvent, ...]
    hypotheses: tuple[QualificationHypothesis, ...]
    protected_criteria: tuple[ProtectedCriterion, ...]
    adverse_measures: tuple[AdverseMeasure, ...]
    comparators: tuple[ComparatorAssessment, ...]
    automatic_questions: tuple[PrioritizedQuestion, ...]
    evidence: tuple[EvidenceRequirement, ...]
    employee_position: ContradictoryPosition
    employer_position: ContradictoryPosition
    strategies: tuple[ProtectionStrategy, ...]
    articulation: DomainArticulation
    missing_information: tuple[str, ...]
    urgency: UrgencyLevel
    confidence: ConfidenceLevel
    scenario_code: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "analysis_type": "discrimination_harassment_equal_treatment",
            "timeline": [
                {
                    "event_id": item.event_id,
                    "kind": item.kind.value,
                    "period": item.period,
                    "precision": item.precision.value,
                    "factual_description": item.factual_description,
                    "nature": item.nature.value,
                    "source": item.source,
                    "people_present": list(item.people_present),
                    "evidence_refs": list(item.evidence_refs),
                    "confidence": item.confidence.value,
                    "related_event_ids": list(item.related_event_ids),
                }
                for item in self.timeline
            ],
            "hypotheses": [
                {
                    "situation": item.situation.value,
                    "supporting_facts": list(item.supporting_facts),
                    "weakening_facts": list(item.weakening_facts),
                    "missing_elements": list(item.missing_elements),
                    "legal_criteria_to_check": list(item.legal_criteria_to_check),
                    "required_evidence": list(item.required_evidence),
                    "alternative_explanations": list(item.alternative_explanations),
                    "confidence": item.confidence.value,
                    "urgency": item.urgency.value,
                    "possible_consequences": list(item.possible_consequences),
                }
                for item in self.hypotheses
            ],
            "protected_criteria": [item.value for item in self.protected_criteria],
            "adverse_measures": [item.value for item in self.adverse_measures],
            "comparators": [
                {
                    "comparator_type": item.comparator_type,
                    "relevance": item.relevance,
                    "similarities": list(item.similarities),
                    "objective_differences": list(item.objective_differences),
                    "missing_data": list(item.missing_data),
                    "reliability": item.reliability.value,
                    "limitations": list(item.limitations),
                    "alternative_explanations": list(item.alternative_explanations),
                }
                for item in self.comparators
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
                    "evidence_type": item.evidence_type,
                    "label": item.label,
                    "category": item.category.value,
                    "utility": item.utility,
                    "can_demonstrate": item.can_demonstrate,
                    "cannot_demonstrate_alone": item.cannot_demonstrate_alone,
                    "reliability": item.reliability.value,
                    "acquisition_risk": item.acquisition_risk,
                }
                for item in self.evidence
            ],
            "employee_position": _position_dict(self.employee_position),
            "employer_position": _position_dict(self.employer_position),
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
                    "competent_actor": item.competent_actor,
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


def _position_dict(position: ContradictoryPosition) -> dict[str, object]:
    return {
        "arguments": list(position.arguments),
        "strengths": list(position.strengths),
        "weaknesses": list(position.weaknesses),
        "evidence": list(position.evidence),
        "missing_evidence": list(position.missing_evidence),
        "foreseeable_objections": list(position.foreseeable_objections),
        "possible_responses": list(position.possible_responses),
        "unresolved_points": list(position.unresolved_points),
    }
