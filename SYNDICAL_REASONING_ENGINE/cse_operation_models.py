"""Immutable contracts for R2B CSE operation and meeting preparation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Protocol

from .models import ConfidenceLevel, SyndicalReasoningReport, UrgencyLevel


class MeetingType(str, Enum):
    ORDINARY = "ordinary"
    EXTRAORDINARY = "extraordinary"
    ELECTED_MEMBERS_REQUEST = "elected_members_request"
    PROJECT_RELATED = "project_related"
    UNKNOWN = "unknown"


class MeetingEventKind(str, Enum):
    AGENDA_REQUEST = "agenda_request"
    AGENDA_DISCUSSION = "agenda_discussion"
    AGENDA_VALIDATION = "agenda_validation"
    CONVOCATION = "convocation"
    DOCUMENT_TRANSMISSION = "document_transmission"
    PREPARATORY_QUESTIONS = "preparatory_questions"
    MEETING = "meeting"
    SUSPENSION = "suspension"
    MANAGEMENT_RESPONSE = "management_response"
    VOTE = "vote"
    OPINION = "opinion"
    RESOLUTION = "resolution"
    MINUTES_DRAFT = "minutes_draft"
    MINUTES_VALIDATION = "minutes_validation"
    MINUTES_DISTRIBUTION = "minutes_distribution"
    COMMITMENT_FOLLOW_UP = "commitment_follow_up"
    REMINDER = "reminder"


class ItemStatus(str, Enum):
    REQUESTED = "requested"
    INCLUDED = "included"
    APPARENTLY_REFUSED = "apparently_refused"
    DEFERRED = "deferred"
    DISCUSSED = "discussed"
    TO_DOCUMENT = "to_document"


class DocumentStatus(str, Enum):
    NOT_TRANSMITTED = "not_transmitted"
    ANNOUNCED = "announced"
    PARTIAL = "partial"
    OUTDATED = "outdated"
    RECEIVED = "received"
    NOT_APPLICABLE = "not_applicable"
    CONFIDENTIALITY_TO_EXAMINE = "confidentiality_to_examine"


class QuestionCategory(str, Enum):
    FACTUAL = "factual"
    PROCEDURAL = "procedural"
    IMPACT = "impact"
    FOLLOW_UP = "follow_up"


class OpinionType(str, Enum):
    FAVORABLE = "favorable"
    FAVORABLE_WITH_RESERVATIONS = "favorable_with_reservations"
    UNFAVORABLE = "unfavorable"
    UNABLE_TO_OPINE = "unable_to_opine"
    CONDITIONAL = "conditional"
    ACKNOWLEDGE_INSUFFICIENT_INFORMATION = "acknowledge_insufficient_information"
    REQUEST_DEFERRAL = "request_deferral"


class CommitmentStatus(str, Enum):
    TO_CONFIRM = "to_confirm"
    RECORDED = "recorded"
    PENDING = "pending"
    PARTIALLY_COMPLETED = "partially_completed"
    COMPLETED = "completed"
    NOT_MET = "not_met"
    DEFERRED = "deferred"
    IMPOSSIBLE_TO_VERIFY = "impossible_to_verify"


class OperationAssessment(str, Enum):
    APPARENTLY_REGULAR = "apparently_regular"
    ISOLATED_DIFFICULTY = "isolated_difficulty"
    POSSIBLE_RECURRING_DYSFUNCTION = "possible_recurring_dysfunction"
    TO_DOCUMENT = "to_document"
    POSSIBLE_OBSTRUCTION_RISK = "possible_obstruction_risk"
    INSUFFICIENT_DATA = "insufficient_data"


class DocumentPriority(str, Enum):
    ESSENTIAL = "essential"
    USEFUL = "useful"
    COMPLEMENTARY = "complementary"


@dataclass(frozen=True, slots=True)
class AgendaItem:
    title: str
    context: str
    precise_questions: tuple[str, ...]
    requested_documents: tuple[str, ...]
    expected_outcome: str
    target_date: str | None
    follow_up: str
    status: ItemStatus = ItemStatus.REQUESTED


@dataclass(frozen=True, slots=True)
class CSEDocument:
    document_type: str
    title: str
    status: DocumentStatus
    received_on: str | None = None
    version: str | None = None
    updated_on: str | None = None
    confidentiality_claimed: bool = False
    utility: str = ""
    limitation: str = ""


@dataclass(frozen=True, slots=True)
class CSEMeetingFacts:
    meeting_type: MeetingType
    scheduled_date: str | None = None
    convocation_date: str | None = None
    convocation_author: str | None = None
    agenda_items: tuple[AgendaItem, ...] = ()
    refused_items: tuple[str, ...] = ()
    documents: tuple[CSEDocument, ...] = ()
    elected_members_present: tuple[str, ...] = ()
    majority_information: str | None = None
    opinion_requested: bool | None = None
    opinion_rendered: bool | None = None
    reservations: tuple[str, ...] = ()
    resolution_declared: bool | None = None
    vote_declared: bool | None = None
    minutes_status: str | None = None
    anomalies: tuple[str, ...] = ()
    actions_already_taken: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MeetingTimelineEvent:
    event_id: str
    date_or_period: str | None
    date_certain: bool
    actor: str
    nature: MeetingEventKind
    associated_document: str | None
    confidence: ConfidenceLevel
    next_deadline: str | None = None
    potential_consequence: str | None = None


@dataclass(frozen=True, slots=True)
class ActorRole:
    actor: str
    primary_actions: tuple[str, ...]
    may_propose: tuple[str, ...] = ()
    may_decide: tuple[str, ...] = ()
    may_vote: bool = False
    may_be_consulted: tuple[str, ...] = ()
    must_receive_information: tuple[str, ...] = ()
    may_remind: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CSEQuestion:
    category: QuestionCategory
    priority: int
    question: str
    purpose: str
    related_documents: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DocumentRequest:
    document_type: str
    utility: str
    answered_question: str
    priority: DocumentPriority
    holder: str
    desired_date: str | None
    confidentiality_note: str
    limitation: str
    action_if_missing: str


@dataclass(frozen=True, slots=True)
class DeadlineAssessment:
    label: str
    starting_point: str | None
    trigger_event: str
    potential_duration: str | None
    source_to_verify: str
    theoretical_date: str | None
    uncertainty: str
    estimated_days_remaining: int | None
    urgency: UrgencyLevel
    recommended_action: str
    legally_calculated: bool = False


@dataclass(frozen=True, slots=True)
class OpinionDraft:
    opinion_type: OpinionType
    project_subject: str
    received_documents: tuple[str, ...]
    missing_information: tuple[str, ...]
    favorable_elements: tuple[str, ...]
    risks_and_reservations: tuple[str, ...]
    requested_commitments: tuple[str, ...]
    follow_up_conditions: tuple[str, ...]
    proposed_position: str
    voting_points: tuple[str, ...]
    new_presentation_request: str | None
    limits: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Reservation:
    subject: str
    observed_fact: str
    missing_information: str
    risk: str
    request: str
    target_date: str | None
    follow_up_indicator: str


@dataclass(frozen=True, slots=True)
class ResolutionDraft:
    factual_basis: tuple[str, ...]
    proposed_decision: str
    execution_owner: str
    target_date: str | None
    associated_document: str | None
    follow_up_method: str
    validity_to_confirm: bool = True


@dataclass(frozen=True, slots=True)
class Commitment:
    wording: str
    author: str
    declared_on: str | None
    source_meeting: str | None
    written: bool
    target_date: str | None
    owner: str
    expected_evidence: str
    status: CommitmentStatus
    reminder: str | None
    result: str | None
    confidence: ConfidenceLevel


@dataclass(frozen=True, slots=True)
class CSEHistoryMetadata:
    title: str
    meeting_date: str | None
    instance: str
    theme: str
    agenda_item: str | None = None
    has_management_response: bool = False
    has_commitment: bool = False
    target_date: str | None = None
    occurrence_count: int = 1

    def __post_init__(self) -> None:
        if not self.title.strip() or not self.instance.strip():
            raise ValueError("history metadata requires a title and instance")
        if self.occurrence_count < 1:
            raise ValueError("occurrence_count must be positive")


class CSEHistoryLookup(Protocol):
    def search_metadata(self, query: str) -> tuple[CSEHistoryMetadata, ...]: ...


@dataclass(frozen=True, slots=True)
class ContradictoryPosition:
    arguments: tuple[str, ...]
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    objections: tuple[str, ...]
    possible_responses: tuple[str, ...]
    compromise_options: tuple[str, ...]
    undecidable_points: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CSEOperationStrategy:
    level: int
    name: str
    objective: str
    actor: str
    urgency: UrgencyLevel
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
class CSEOperationAnalysis:
    base_report: SyndicalReasoningReport
    meeting: CSEMeetingFacts
    timeline: tuple[MeetingTimelineEvent, ...]
    actor_roles: tuple[ActorRole, ...]
    agenda_proposals: tuple[AgendaItem, ...]
    questions: tuple[CSEQuestion, ...]
    document_requests: tuple[DocumentRequest, ...]
    deadlines: tuple[DeadlineAssessment, ...]
    opinion_drafts: tuple[OpinionDraft, ...]
    reservations: tuple[Reservation, ...]
    resolutions: tuple[ResolutionDraft, ...]
    commitments: tuple[Commitment, ...]
    history: tuple[CSEHistoryMetadata, ...]
    elected_position: ContradictoryPosition
    employer_position: ContradictoryPosition
    operation_assessment: OperationAssessment
    strategies: tuple[CSEOperationStrategy, ...]
    articulation: DomainArticulation
    missing_information: tuple[str, ...]
    urgency: UrgencyLevel
    confidence: ConfidenceLevel
    scenario_code: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("base_report")
        return {"analysis_type": "cse_operation_meeting_preparation", **_serialize(payload)}


def _serialize(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value
