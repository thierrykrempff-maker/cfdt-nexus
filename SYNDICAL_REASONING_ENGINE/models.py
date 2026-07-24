"""Immutable public contracts for the Syndical Reasoning Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class UrgencyLevel(str, Enum):
    ROUTINE = "routine"
    PROMPT = "prompt"
    URGENT = "urgent"
    IMMEDIATE = "immediate"


class ConfidentialityLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class FactStatus(str, Enum):
    DECLARED = "declared"
    ESTABLISHED = "established"
    HYPOTHESIS = "hypothesis"


class SourceVerification(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    MISSING = "missing"


@dataclass(frozen=True, slots=True)
class CaseFact:
    """A neutral fact or hypothesis; no inference is hidden in the model."""

    statement: str
    status: FactStatus = FactStatus.DECLARED
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.statement.strip():
            raise ValueError("fact statement must be non-empty")


@dataclass(frozen=True, slots=True)
class AvailablePiece:
    """Metadata-only reference to a piece available for the analysis."""

    piece_id: str
    document_type: str
    title: str
    confidentiality: ConfidentialityLevel = ConfidentialityLevel.INTERNAL
    verified: bool = False

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.piece_id, self.document_type, self.title)):
            raise ValueError("piece metadata must be non-empty")


@dataclass(frozen=True, slots=True)
class SourceReference:
    """Traceable source metadata; document content is deliberately absent."""

    source_id: str
    title: str
    source_type: str
    authority: str
    canonical_url: str | None = None
    verification: SourceVerification = SourceVerification.UNVERIFIED
    internal: bool = False
    effective_on: str | None = None
    contradicts_source_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (self.source_id, self.title, self.source_type, self.authority)
        ):
            raise ValueError("source metadata must be non-empty")
        if self.canonical_url is not None and not self.canonical_url.startswith("https://"):
            raise ValueError("source URL must use HTTPS")


@dataclass(frozen=True, slots=True)
class Citation:
    """Public, metadata-only citation attached to an important conclusion."""

    source_id: str
    title: str
    authority: str
    canonical_url: str | None
    verification: SourceVerification


@dataclass(frozen=True, slots=True)
class SyndicalCaseInput:
    """Incomplete-by-design input contract for a union-representation case."""

    question: str
    declared_facts: tuple[CaseFact, ...] = ()
    established_facts: tuple[CaseFact, ...] = ()
    hypotheses: tuple[CaseFact, ...] = ()
    person_capacity: str | None = None
    workplace_context: str | None = None
    fact_period: str | None = None
    suspected_domains: tuple[str, ...] = ()
    available_pieces: tuple[AvailablePiece, ...] = ()
    available_internal_sources: tuple[SourceReference, ...] = ()
    available_sources: tuple[SourceReference, ...] = ()
    urgency: UrgencyLevel = UrgencyLevel.ROUTINE
    confidentiality: ConfidentialityLevel = ConfidentialityLevel.INTERNAL
    desired_outcome: str | None = None
    missing_information: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.question.strip():
            raise ValueError("question must be non-empty")
        for fact in self.declared_facts:
            if fact.status is not FactStatus.DECLARED:
                raise ValueError("declared facts must have DECLARED status")
        for fact in self.established_facts:
            if fact.status is not FactStatus.ESTABLISHED:
                raise ValueError("established facts must have ESTABLISHED status")
        for fact in self.hypotheses:
            if fact.status is not FactStatus.HYPOTHESIS:
                raise ValueError("hypotheses must have HYPOTHESIS status")


@dataclass(frozen=True, slots=True)
class SourceAssessment:
    source: SourceReference
    rank: int
    rationale: str


@dataclass(frozen=True, slots=True)
class SourceContradiction:
    source_ids: tuple[str, ...]
    subject: str
    requires_review: bool = True


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    category: str
    level: UrgencyLevel
    rationale: str


@dataclass(frozen=True, slots=True)
class ActionOption:
    name: str
    objective: str
    competent_actor: str
    prerequisites: tuple[str, ...]
    required_pieces: tuple[str, ...]
    advantages: tuple[str, ...]
    limitations: tuple[str, ...]
    risks: tuple[str, ...]
    urgency: UrgencyLevel
    reversible: bool
    recommended_order: int
    document_template: str | None = None


@dataclass(frozen=True, slots=True)
class ActionPlanStep:
    order: int
    action: str
    actor: str
    condition: str


@dataclass(frozen=True, slots=True)
class SyndicalReasoningReport:
    """Complete non-decisional output, suitable for short and expert views."""

    situation_summary: str
    retained_facts: tuple[str, ...]
    hypotheses: tuple[str, ...]
    missing_information: tuple[str, ...]
    provisional_qualification: tuple[str, ...]
    domains: tuple[str, ...]
    main_issues: tuple[str, ...]
    sources: tuple[SourceAssessment, ...]
    source_hierarchy: tuple[str, ...]
    contradictions: tuple[SourceContradiction, ...]
    possible_employee_rights: tuple[str, ...]
    employer_obligations_or_risks: tuple[str, ...]
    representative_roles: tuple[str, ...]
    urgency: UrgencyLevel
    confidence: ConfidenceLevel
    action_options: tuple[ActionOption, ...]
    recommended_strategy: str
    action_plan: tuple[ActionPlanStep, ...]
    evidence_to_obtain: tuple[str, ...]
    follow_up_questions: tuple[str, ...]
    caution_alerts: tuple[str, ...]
    citations: tuple[Citation, ...]
    analysis_limits: tuple[str, ...]
    completed_steps: tuple[str, ...]

    def short_view(self) -> dict[str, object]:
        return {
            "situation": self.situation_summary,
            "qualification": list(self.provisional_qualification),
            "urgence": self.urgency.value,
            "confiance": self.confidence.value,
            "strategie": self.recommended_strategy,
            "prochaines_actions": [
                {"ordre": item.order, "action": item.action, "acteur": item.actor}
                for item in self.action_plan[:4]
            ],
            "incertitudes": list(self.analysis_limits),
            "citations": [
                {
                    "title": item.title,
                    "authority": item.authority,
                    "url": item.canonical_url,
                    "verification": item.verification.value,
                }
                for item in self.citations
            ],
        }

    def expert_view(self) -> dict[str, object]:
        return {
            **self.short_view(),
            "faits_retenus": list(self.retained_facts),
            "hypotheses": list(self.hypotheses),
            "informations_manquantes": list(self.missing_information),
            "domaines": list(self.domains),
            "enjeux": list(self.main_issues),
            "hierarchie_sources": list(self.source_hierarchy),
            "contradictions": [
                {
                    "source_ids": list(item.source_ids),
                    "subject": item.subject,
                    "requires_review": item.requires_review,
                }
                for item in self.contradictions
            ],
            "droits_possibles": list(self.possible_employee_rights),
            "obligations_risques_employeur": list(self.employer_obligations_or_risks),
            "roles_representants": list(self.representative_roles),
            "options": [
                {
                    "name": item.name,
                    "actor": item.competent_actor,
                    "order": item.recommended_order,
                    "reversible": item.reversible,
                    "risks": list(item.risks),
                }
                for item in self.action_options
            ],
            "preuves_a_obtenir": list(self.evidence_to_obtain),
            "questions": list(self.follow_up_questions),
            "alertes": list(self.caution_alerts),
            "limites": list(self.analysis_limits),
            "etapes": list(self.completed_steps),
        }
