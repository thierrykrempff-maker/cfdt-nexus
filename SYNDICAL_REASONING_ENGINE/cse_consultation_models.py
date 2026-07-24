"""Immutable, metadata-only contracts for the R2A CSE consultation domain."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Protocol

from .models import ConfidenceLevel, SyndicalReasoningReport, UrgencyLevel


class ProjectType(str, Enum):
    REORGANIZATION = "reorganization"
    JOB_CHANGES = "job_changes"
    WORKING_TIME = "working_time"
    OUTSOURCING = "outsourcing"
    RELOCATION = "relocation"
    MONITORING_TOOL = "monitoring_tool"
    WORK_METHOD = "work_method"
    STAFFING = "staffing"
    ECONOMIC_PROJECT = "economic_project"
    UNKNOWN = "unknown"


class CollectiveDimension(str, Enum):
    ISOLATED_INDIVIDUAL = "isolated_individual"
    REPEATED_INDIVIDUAL_CASES = "repeated_individual_cases"
    GENERAL_PRACTICE = "general_practice"
    IDENTIFIED_COLLECTIVE_PROJECT = "identified_collective_project"
    COLLECTIVE_PROJECT_NOT_DEMONSTRATED = "collective_project_not_demonstrated"


class ParticipationMechanism(str, Enum):
    INFORMATION = "information"
    CONSULTATION = "consultation"
    RECURRING_CONSULTATION = "recurring_consultation"
    COLLECTIVE_BARGAINING = "collective_bargaining"
    MANAGEMENT_POWER = "management_power"
    TO_BE_CONFIRMED = "to_be_confirmed"


class ConsultationAssessment(str, Enum):
    APPARENTLY_REGULAR = "apparently_regular"
    TO_DOCUMENT = "to_document"
    POSSIBLY_INSUFFICIENT_INFORMATION = "possibly_insufficient_information"
    POTENTIALLY_LATE = "potentially_late"
    POSSIBLE_EARLY_IMPLEMENTATION = "possible_early_implementation"
    APPARENT_ABSENCE = "apparent_absence"
    INSUFFICIENT_DATA = "insufficient_data"


class EventNature(str, Enum):
    RUMOUR = "rumour"
    EMPLOYEE_STATEMENT = "employee_statement"
    MANAGEMENT_ANNOUNCEMENT = "management_announcement"
    OFFICIAL_INFORMATION = "official_information"
    DOCUMENT_TRANSMISSION = "document_transmission"
    AGENDA_LISTING = "agenda_listing"
    CSE_MEETING = "cse_meeting"
    DOCUMENT_REQUEST = "document_request"
    MANAGEMENT_RESPONSE = "management_response"
    CSE_OPINION = "cse_opinion"
    FORMALISED_DECISION = "formalised_decision"
    IMPLEMENTATION = "implementation"
    OBSERVED_CONSEQUENCE = "observed_consequence"
    CHALLENGE = "challenge"
    EXTERNAL_REFERRAL = "external_referral"


class QuestionPriority(str, Enum):
    CRITICAL = "critical"
    PRIORITY = "priority"
    USEFUL = "useful"
    COMPLEMENTARY = "complementary"


class DocumentPriority(str, Enum):
    ESSENTIAL = "essential"
    USEFUL = "useful"
    COMPLEMENTARY = "complementary"


class ObstructionRisk(str, Enum):
    NONE_IDENTIFIED = "none_identified"
    TO_VERIFY = "to_verify"
    POSSIBLE_INDICATORS = "possible_indicators"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True, slots=True)
class CSEProjectFacts:
    project_type: ProjectType
    signal_origin: str
    employees_affected: int | None = None
    affected_services: tuple[str, ...] = ()
    decision_envisaged: bool | None = None
    decision_already_taken: bool | None = None
    implementation_started: bool | None = None
    announcement_date: str | None = None
    implementation_date: str | None = None
    cse_information_known: bool | None = None
    cse_consultation_known: bool | None = None
    opinion_rendered: bool | None = None
    transmitted_documents: tuple[str, ...] = ()
    missing_documents: tuple[str, ...] = ()
    employment_impacts: tuple[str, ...] = ()
    schedule_impacts: tuple[str, ...] = ()
    remuneration_impacts: tuple[str, ...] = ()
    working_condition_impacts: tuple[str, ...] = ()
    health_safety_signals: tuple[str, ...] = ()
    potentially_applicable_agreements: tuple[str, ...] = ()
    recurring_consultation: bool | None = None
    actions_already_taken: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProjectTimelineEvent:
    event_id: str
    date_or_period: str | None
    date_certain: bool
    actor: str
    nature: EventNature
    associated_document: str | None
    confidence: ConfidenceLevel
    consequences: tuple[str, ...] = ()
    next_deadline: str | None = None


@dataclass(frozen=True, slots=True)
class CSEQualification:
    label: str
    supporting_facts: tuple[str, ...]
    weakening_facts: tuple[str, ...]
    missing_information: tuple[str, ...]
    sources_to_verify: tuple[str, ...]
    documents_needed: tuple[str, ...]
    alternative_explanations: tuple[str, ...]
    confidence: ConfidenceLevel
    urgency: UrgencyLevel
    potential_consequences: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CSEQuestion:
    priority: QuestionPriority
    question: str
    purpose: str


@dataclass(frozen=True, slots=True)
class DocumentRequest:
    document_type: str
    priority: DocumentPriority
    utility: str
    answered_question: str
    limitation: str
    holder: str
    request_reason: str


@dataclass(frozen=True, slots=True)
class CSEMemoryMetadata:
    document_id: str
    title: str
    document_type: str
    year: int | None = None
    instance: str | None = None
    theme: str | None = None
    has_commitment: bool = False
    has_management_response: bool = False
    occurrence_count: int = 1

    def __post_init__(self) -> None:
        if not self.document_id.strip() or not self.title.strip():
            raise ValueError("CSE memory metadata requires a stable id and title")
        if self.occurrence_count < 1:
            raise ValueError("occurrence_count must be positive")


class CSEMemoryLookup(Protocol):
    """Read-only boundary; implementations return metadata, never document content."""

    def search_metadata(self, query: str) -> tuple[CSEMemoryMetadata, ...]: ...


@dataclass(frozen=True, slots=True)
class MechanismAnalysis:
    mechanism: ParticipationMechanism
    competent_actor: str
    intervention_moment: str
    required_documents: tuple[str, ...]
    points_to_confirm: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ContradictoryPosition:
    arguments: tuple[str, ...]
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    objections: tuple[str, ...]
    possible_responses: tuple[str, ...]
    undecidable_points: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ObstructionAssessment:
    risk: ObstructionRisk
    observed_facts: tuple[str, ...]
    missing_facts: tuple[str, ...]
    alternative_explanations: tuple[str, ...]
    prior_actions: tuple[str, ...]
    competent_actor: str
    legal_review_recommended: bool = True


@dataclass(frozen=True, slots=True)
class CSEStrategy:
    level: int
    name: str
    objective: str
    urgency: UrgencyLevel
    actor: str
    advantages: tuple[str, ...]
    limitations: tuple[str, ...]
    risks: tuple[str, ...]
    required_pieces: tuple[str, ...]
    expected_result: str
    next_step: str


@dataclass(frozen=True, slots=True)
class DomainArticulation:
    primary_domain: str
    complementary_domains: tuple[str, ...]
    rationale: str
    common_caution: str


@dataclass(frozen=True, slots=True)
class CSEConsultationAnalysis:
    base_report: SyndicalReasoningReport
    project: CSEProjectFacts
    collective_dimension: CollectiveDimension
    timeline: tuple[ProjectTimelineEvent, ...]
    qualifications: tuple[CSEQualification, ...]
    mechanism: MechanismAnalysis
    consultation_assessment: ConsultationAssessment
    automatic_questions: tuple[CSEQuestion, ...]
    document_requests: tuple[DocumentRequest, ...]
    cse_memory_results: tuple[CSEMemoryMetadata, ...]
    cse_employee_position: ContradictoryPosition
    employer_position: ContradictoryPosition
    obstruction: ObstructionAssessment
    strategies: tuple[CSEStrategy, ...]
    articulation: DomainArticulation
    missing_information: tuple[str, ...]
    urgency: UrgencyLevel
    confidence: ConfidenceLevel
    scenario_code: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("base_report")
        payload["cse_memory_results"] = [
            {
                "title": item.title,
                "document_type": item.document_type,
                "year": item.year,
                "instance": item.instance,
                "theme": item.theme,
                "has_commitment": item.has_commitment,
                "has_management_response": item.has_management_response,
                "occurrence_count": item.occurrence_count,
            }
            for item in self.cse_memory_results
        ]
        return {
            "analysis_type": "cse_information_consultation_reorganization",
            **_serialize(payload),
        }


def _serialize(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value
