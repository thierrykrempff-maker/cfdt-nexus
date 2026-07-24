"""Immutable R2C contracts for claims, alerts, expertise and escalation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Protocol

from .models import ConfidenceLevel, SyndicalReasoningReport, UrgencyLevel


class ClaimScope(str, Enum):
    INDIVIDUAL_REQUEST = "individual_request"
    INDIVIDUAL_CLAIM = "individual_claim"
    REPEATED_SIMILAR_CLAIMS = "repeated_similar_claims"
    COLLECTIVE_CLAIM = "collective_claim"
    UNION_DEMAND = "union_demand"
    COLLECTIVE_BARGAINING = "collective_bargaining"
    CSE_MATTER = "cse_matter"
    INDIVIDUAL_LITIGATION = "individual_litigation"
    TO_INVESTIGATE = "to_investigate"


class AlertMechanism(str, Enum):
    RIGHTS_OF_PERSONS = "potential_rights_of_persons_alert"
    ECONOMIC = "potential_economic_alert"
    SOCIAL = "potential_social_alert"
    DEGRADED_CSE_FUNCTIONING = "degraded_cse_functioning"
    COLLECTIVE_RISK = "collective_risk_without_cssct_qualification"
    SIMPLE_CLAIM = "simple_claim"
    INFORMATION_REQUEST = "information_request"
    INVESTIGATION_FIRST = "investigation_first"


class ExpertiseKind(str, Enum):
    RECURRING_CONSULTATION = "recurring_consultation"
    OCCASIONAL_CONSULTATION = "occasional_consultation"
    ECONOMIC_ACCOUNTING = "economic_accounting"
    RESTRUCTURING = "restructuring"
    IMPORTANT_PROJECT = "important_project"
    POTENTIAL_SERIOUS_RISK = "potential_serious_risk_without_cssct_analysis"
    CSE_FUNDED = "cse_funded"
    EXTERNAL_LEGAL_TECHNICAL_SUPPORT = "external_legal_technical_support"


class InvestigationKind(str, Enum):
    INTERNAL = "internal"
    CSE = "cse"
    JOINT = "joint"
    DISCIPLINARY = "disciplinary"
    SIGNAL_RELATED = "signal_related"
    DOCUMENTARY = "documentary"
    EXTERNAL_LEGAL = "external_legal"
    FUTURE_CSSCT = "future_cssct"


class EscalationKind(str, Enum):
    INTERNAL_REMINDER = "internal_reminder"
    CSE_RESOLUTION = "cse_resolution"
    FORMAL_DOCUMENT_REQUEST = "formal_document_request"
    EXTRAORDINARY_MEETING = "extraordinary_meeting"
    UNION_INTERVENTION = "union_intervention"
    NEGOTIATION_REQUEST = "negotiation_request"
    LABOUR_INSPECTORATE = "labour_inspectorate"
    DEFENDER_OF_RIGHTS = "defender_of_rights"
    OCCUPATIONAL_HEALTH = "occupational_health"
    SOCIAL_SECURITY_BODY = "social_security_body"
    LEGAL_COUNSEL = "legal_counsel"
    EXPERT = "expert"
    COURT = "court"
    ADMINISTRATIVE_AUTHORITY = "administrative_authority"


class AlertEventKind(str, Enum):
    FIRST_SIGNAL = "first_signal"
    INDIVIDUAL_CLAIM = "individual_claim"
    REPEATED_SIGNAL = "repeated_signal"
    COLLECTIVE_EXTENSION = "collective_extension"
    CSE_REFERRAL = "cse_referral"
    AGENDA_REGISTRATION = "agenda_registration"
    MANAGEMENT_RESPONSE = "management_response"
    DOCUMENT_REQUEST = "document_request"
    DOCUMENT_RESPONSE = "document_response"
    RESOLUTION = "resolution"
    FORMAL_ALERT = "formal_alert"
    INVESTIGATION = "investigation"
    EXPERT_REFERRAL = "expert_referral"
    EXTERNAL_REFERRAL = "external_referral"
    EMPLOYER_COMMITMENT = "employer_commitment"
    DEADLINE = "deadline"
    REMINDER = "reminder"
    NO_FOLLOW_UP = "no_follow_up"
    CORRECTIVE_MEASURE = "corrective_measure"
    PROVISIONAL_CLOSURE = "provisional_closure"
    FINAL_CLOSURE = "final_closure"


class SeverityLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH_TO_CONFIRM = "high_to_confirm"
    UNDETERMINED = "undetermined"


class EvidenceStrength(str, Enum):
    DECLARED = "declared"
    PARTIAL = "partial"
    CORROBORATED = "corroborated"
    DOCUMENTED = "documented"
    INSUFFICIENT = "insufficient"


class QuestionPriority(str, Enum):
    CRITICAL = "critical"
    PRIORITY = "priority"
    USEFUL = "useful"
    COMPLEMENTARY = "complementary"


class DocumentPriority(str, Enum):
    ESSENTIAL = "essential"
    USEFUL = "useful"
    COMPLEMENTARY = "complementary"


@dataclass(frozen=True, slots=True)
class ClaimSignal:
    scope: ClaimScope
    origin: str
    employees_count: int | None
    affected_services: tuple[str, ...]
    declared_facts: tuple[str, ...]
    repeated: bool | None
    duration: str | None
    consequences: tuple[str, ...]
    potentially_affected_rights: tuple[str, ...]
    actions_already_taken: tuple[str, ...]
    employer_response: str | None
    common_source: str | None
    collective_effect: str | None
    confidence: ConfidenceLevel


@dataclass(frozen=True, slots=True)
class AlertHypothesis:
    mechanism: AlertMechanism
    cautious_qualification: str
    possible_triggers: tuple[str, ...]
    criteria_to_verify: tuple[str, ...]
    competent_actor: str
    required_documents: tuple[str, ...]
    possible_steps: tuple[str, ...]
    limitations: tuple[str, ...]
    confidence: ConfidenceLevel
    legal_review_required: bool = True
    automatically_established: bool = False


@dataclass(frozen=True, slots=True)
class ExpertiseHypothesis:
    kind: ExpertiseKind
    purpose: str
    potential_basis: str
    favorable_facts: tuple[str, ...]
    unfavorable_facts: tuple[str, ...]
    required_documents: tuple[str, ...]
    potential_deadline: str | None
    funding_to_verify: str
    deciding_actor: str
    risks: tuple[str, ...]
    legal_review_required: bool
    confidence: ConfidenceLevel
    automatically_acquired: bool = False


@dataclass(frozen=True, slots=True)
class InvestigationProposal:
    kind: InvestigationKind
    purpose: str
    actors: tuple[str, ...]
    scope: str
    documents: tuple[str, ...]
    people_to_hear: tuple[str, ...]
    precautions: tuple[str, ...]
    confidentiality: str
    neutrality: str
    report_method: str
    follow_up: str
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EscalationOption:
    kind: EscalationKind
    competence: str
    objective: str
    prerequisites: tuple[str, ...]
    required_pieces: tuple[str, ...]
    urgency: UrgencyLevel
    advantages: tuple[str, ...]
    limitations: tuple[str, ...]
    risks: tuple[str, ...]
    expected_result: str
    alternative: str


@dataclass(frozen=True, slots=True)
class AlertTimelineEvent:
    event_id: str
    date_or_period: str | None
    date_certain: bool
    actor: str
    kind: AlertEventKind
    source: str | None
    confidence: ConfidenceLevel
    consequence: str | None
    next_deadline: str | None
    status: str


@dataclass(frozen=True, slots=True)
class CompetentActor:
    name: str
    competence: str
    possible_actions: tuple[str, ...]
    limits: tuple[str, ...]
    external: bool = False


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    evidence_type: str
    description: str
    source: str
    strength: EvidenceStrength
    verified: bool
    limitation: str


@dataclass(frozen=True, slots=True)
class AlertDocumentRequest:
    document_type: str
    utility: str
    priority: DocumentPriority
    holder: str
    confidentiality: str
    limitation: str
    action_if_missing: str


@dataclass(frozen=True, slots=True)
class AlertQuestion:
    priority: QuestionPriority
    wording: str
    purpose: str
    related_documents: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlertResolutionDraft:
    resolution_type: str
    known_facts: tuple[str, ...]
    facts_to_verify: tuple[str, ...]
    purpose: str
    missing_documents: tuple[str, ...]
    proposed_decision: str
    responsible_actor: str
    target_deadline: str | None
    follow_up: str
    reservations: tuple[str, ...]
    legal_review_required: bool = True
    draft_only: bool = True


@dataclass(frozen=True, slots=True)
class AlertHistoryMetadata:
    title: str
    meeting_date: str | None
    theme: str
    has_signal: bool = False
    has_resolution: bool = False
    has_commitment: bool = False
    has_expertise: bool = False
    has_management_response: bool = False
    target_date: str | None = None
    occurrence_count: int = 1

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("history metadata requires a title")
        if self.occurrence_count < 1:
            raise ValueError("occurrence_count must be positive")


class AlertHistoryLookup(Protocol):
    def search_metadata(self, query: str) -> tuple[AlertHistoryMetadata, ...]: ...


@dataclass(frozen=True, slots=True)
class AlertContradictoryAnalysis:
    arguments: tuple[str, ...]
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    objections: tuple[str, ...]
    possible_responses: tuple[str, ...]
    evidence_to_decide: tuple[str, ...]
    undecidable_points: tuple[str, ...]
    compromise_options: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlertStrategy:
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
class AlertDomainArticulation:
    primary_domain: str
    complementary_domains: tuple[str, ...]
    rationale: str
    common_caution: str


@dataclass(frozen=True, slots=True)
class CSEAlertsExpertiseAnalysis:
    base_report: SyndicalReasoningReport
    claim: ClaimSignal
    timeline: tuple[AlertTimelineEvent, ...]
    alert_hypotheses: tuple[AlertHypothesis, ...]
    expertise_hypotheses: tuple[ExpertiseHypothesis, ...]
    investigations: tuple[InvestigationProposal, ...]
    escalation_options: tuple[EscalationOption, ...]
    competent_actors: tuple[CompetentActor, ...]
    evidence: tuple[EvidenceItem, ...]
    questions: tuple[AlertQuestion, ...]
    document_requests: tuple[AlertDocumentRequest, ...]
    resolutions: tuple[AlertResolutionDraft, ...]
    history: tuple[AlertHistoryMetadata, ...]
    cse_position: AlertContradictoryAnalysis
    employer_position: AlertContradictoryAnalysis
    strategies: tuple[AlertStrategy, ...]
    articulation: AlertDomainArticulation
    severity: SeverityLevel
    urgency: UrgencyLevel
    confidence: ConfidenceLevel
    legal_review_required: bool
    missing_information: tuple[str, ...]
    scenario_code: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("base_report")
        return {"analysis_type": "cse_claims_alerts_expertise", **_serialize(payload)}


def _serialize(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value
