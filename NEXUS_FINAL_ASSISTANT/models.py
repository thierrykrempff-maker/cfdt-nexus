"""Immutable public contracts for the CFDT Nexus final assistant."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class Domain(str, Enum):
    CONTRACT = "contract_conditions"
    DISCIPLINE = "discipline"
    WORKING_TIME = "working_time"
    DISCRIMINATION = "discrimination_harassment"
    HEALTH = "health_absence"
    CSE_CONSULTATION = "cse_consultation"
    CSE_OPERATION = "cse_operation"
    CSE_ALERTS = "cse_alerts"
    PAYROLL = "payroll"
    DOCUMENTARY = "documentary"
    TRANSVERSAL = "transversal"


class Confidence(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ResponseMode(str, Enum):
    QUICK = "QUICK"
    CASE = "CASE"
    EXPERT = "EXPERT"


class PrivacyDecision(str, Enum):
    ALLOWED = "ALLOWED"
    ANONYMIZE = "ANONYMIZE_REQUIRED"
    BLOCKED = "BLOCKED"


class QuestionPriority(str, Enum):
    CRITICAL = "CRITICAL"
    PRIORITY = "PRIORITY"
    USEFUL = "USEFUL"
    COMPLEMENTARY = "COMPLEMENTARY"


@dataclass(frozen=True, slots=True)
class Fact:
    statement: str
    documented: bool = False
    source: str = "user_statement"


@dataclass(frozen=True, slots=True)
class AssistantRequest:
    question: str
    context: tuple[tuple[str, str], ...] = ()
    user_type: str = "employee"
    union_role: str | None = None
    collective_case: bool = False
    facts: tuple[Fact, ...] = ()
    available_documents: tuple[str, ...] = ()
    period: str | None = None
    declared_urgency: str | None = None
    expected_output: str = "analysis"
    requested_detail: str = "auto"
    allowed_engines: tuple[str, ...] = ()
    prohibited_data: tuple[str, ...] = ()
    confidential_mode: bool = True
    history_available: bool = False
    route_domains: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.question.strip():
            raise ValueError("question must not be empty")


@dataclass(frozen=True, slots=True)
class DomainMatch:
    domain: Domain
    score: int
    triggers: tuple[str, ...]
    contrary_indicators: tuple[str, ...]
    confidence: Confidence
    role: str
    proposed_engine: str
    selection_reason: str
    exclusion_reason: str | None = None


@dataclass(frozen=True, slots=True)
class AnalysisPlan:
    primary_domain: Domain
    complementary_domains: tuple[Domain, ...]
    execution_order: tuple[str, ...]
    sources_to_search: tuple[str, ...]
    critical_questions: tuple[str, ...]
    missing_data: tuple[str, ...]
    calculations_allowed: bool
    excluded_engines: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    fallback: str
    response_mode: ResponseMode


@dataclass(frozen=True, slots=True)
class SourceItem:
    source_type: str
    title: str
    date: str | None = None
    relevance: str = "support"
    reasoning_role: str = "to_verify"
    reliability: int = 0
    document_to_verify: str | None = None
    confidential: bool = False


@dataclass(frozen=True, slots=True)
class NormalizedEngineResult:
    engine: str
    domain: Domain
    available: bool = True
    retained_facts: tuple[str, ...] = ()
    possible_qualifications: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()
    sources: tuple[SourceItem, ...] = ()
    evidence: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    employee_arguments: tuple[str, ...] = ()
    employer_arguments: tuple[str, ...] = ()
    strategies: tuple[str, ...] = ()
    urgencies: tuple[str, ...] = ()
    possible_actions: tuple[str, ...] = ()
    confidence: Confidence = Confidence.LOW
    limits: tuple[str, ...] = ()
    technical_errors: tuple[str, ...] = ()
    metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class Conflict:
    conflict_type: str
    engines: tuple[str, ...]
    explanation: str
    resolution: str
    information_needed: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FusedQuestion:
    text: str
    priority: QuestionPriority
    reason: str


@dataclass(frozen=True, slots=True)
class ActionDraft:
    action_type: str
    subject: str
    context: tuple[str, ...]
    verified_facts: tuple[str, ...]
    facts_to_confirm: tuple[str, ...]
    requests: tuple[str, ...]
    deadline: str | None
    attachments: tuple[str, ...]
    prudence: str
    notice: str = "Brouillon à relire et adapter."


@dataclass(frozen=True, slots=True)
class CriticResult:
    validated_points: tuple[str, ...]
    fragile_points: tuple[str, ...]
    required_corrections: tuple[str, ...]
    publication_verdict: str


@dataclass(frozen=True, slots=True)
class TechnicalTrace:
    engines_planned: tuple[str, ...]
    engines_called: tuple[str, ...]
    engines_failed: tuple[str, ...]
    fallback_used: bool
    max_engines: int


@dataclass(frozen=True, slots=True)
class FinalAssistantResponse:
    request: AssistantRequest
    plan: AnalysisPlan
    domain_matches: tuple[DomainMatch, ...]
    engine_results: tuple[NormalizedEngineResult, ...]
    conflicts: tuple[Conflict, ...]
    sources: tuple[SourceItem, ...]
    questions: tuple[FusedQuestion, ...]
    summary: Mapping[str, tuple[str, ...]]
    actions: tuple[ActionDraft, ...]
    critic: CriticResult
    privacy: PrivacyDecision
    confidence: Confidence
    trace: TechnicalTrace
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_domain": self.plan.primary_domain.value,
            "complementary_domains": [item.value for item in self.plan.complementary_domains],
            "response_mode": self.plan.response_mode.value,
            "confidence": self.confidence.value,
            "privacy": self.privacy.value,
            "domains": [
                {
                    "domain": item.domain.value,
                    "score": item.score,
                    "triggers": list(item.triggers),
                    "contrary_indicators": list(item.contrary_indicators),
                    "confidence": item.confidence.value,
                    "role": item.role,
                    "engine": item.proposed_engine,
                    "selection_reason": item.selection_reason,
                    "exclusion_reason": item.exclusion_reason,
                }
                for item in self.domain_matches
            ],
            "plan": {
                "execution_order": list(self.plan.execution_order),
                "sources_to_search": list(self.plan.sources_to_search),
                "missing_data": list(self.plan.missing_data),
                "calculations_allowed": self.plan.calculations_allowed,
                "excluded_engines": list(self.plan.excluded_engines),
                "fallback": self.plan.fallback,
            },
            "summary": {key: list(value) for key, value in self.summary.items()},
            "questions": [
                {"text": item.text, "priority": item.priority.value, "reason": item.reason}
                for item in self.questions
            ],
            "sources": [
                {
                    "type": item.source_type,
                    "title": item.title,
                    "date": item.date,
                    "relevance": item.relevance,
                    "reasoning_role": item.reasoning_role,
                    "reliability": item.reliability,
                    "document_to_verify": item.document_to_verify,
                    "confidential": item.confidential,
                }
                for item in self.sources
            ],
            "conflicts": [
                {
                    "type": item.conflict_type,
                    "engines": list(item.engines),
                    "explanation": item.explanation,
                    "resolution": item.resolution,
                    "information_needed": list(item.information_needed),
                }
                for item in self.conflicts
            ],
            "actions": [
                {
                    "type": item.action_type,
                    "subject": item.subject,
                    "context": list(item.context),
                    "verified_facts": list(item.verified_facts),
                    "facts_to_confirm": list(item.facts_to_confirm),
                    "requests": list(item.requests),
                    "deadline": item.deadline,
                    "attachments": list(item.attachments),
                    "prudence": item.prudence,
                    "notice": item.notice,
                }
                for item in self.actions
            ],
            "critic": {
                "validated_points": list(self.critic.validated_points),
                "fragile_points": list(self.critic.fragile_points),
                "required_corrections": list(self.critic.required_corrections),
                "publication_verdict": self.critic.publication_verdict,
            },
            "trace": {
                "engines_planned": list(self.trace.engines_planned),
                "engines_called": list(self.trace.engines_called),
                "engines_failed": list(self.trace.engines_failed),
                "fallback_used": self.trace.fallback_used,
                "max_engines": self.trace.max_engines,
            },
            "warnings": list(self.warnings),
        }
