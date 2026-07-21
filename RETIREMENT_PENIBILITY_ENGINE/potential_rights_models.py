"""Immutable models for non-decisional potential-rights analysis.

All maturity information concerns the documentary case, never the worker.
No model contains a retirement date, pension amount or calculated C2P value.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .career_evidence_models import EvidenceBundle
from .career_timeline_models import CareerTimeline
from .document_knowledge_models import KnowledgeContext
from .rule_reasoning_models import ReasoningReport


class PotentialRightCategory(str, Enum):
    """Generic schemes that may warrant examination."""

    LEGAL_RETIREMENT = "LEGAL_RETIREMENT"
    LONG_CAREER = "LONG_CAREER"
    PROGRESSIVE_RETIREMENT = "PROGRESSIVE_RETIREMENT"
    INEOS_END_OF_CAREER = "INEOS_END_OF_CAREER"
    C2P = "C2P"
    ATMP = "ATMP"
    NIGHT_WORK = "NIGHT_WORK"
    PREVENTION = "PREVENTION"
    RECLASSIFICATION = "RECLASSIFICATION"
    RETIREMENT_INDEMNITY = "RETIREMENT_INDEMNITY"
    CAREER_CORRECTION = "CAREER_CORRECTION"
    OTHER_SCHEME = "OTHER_SCHEME"


class PotentialRightStatus(str, Enum):
    """Cautious status that never attributes an entitlement."""

    TO_EXAMINE = "TO_EXAMINE"
    INFORMATION_MISSING = "INFORMATION_MISSING"
    OFFICIAL_VALIDATION_REQUIRED = "OFFICIAL_VALIDATION_REQUIRED"
    CONFLICTED = "CONFLICTED"
    NOT_RETAINED = "NOT_RETAINED"


class PotentialRightPriority(str, Enum):
    """Qualitative review order without legal weighting."""

    HIGH = "HIGH"
    NORMAL = "NORMAL"
    CONTEXTUAL = "CONTEXTUAL"


class CaseMaturityLevel(str, Enum):
    """Quality level of the case file, not of the employee."""

    COMPLETE = "COMPLETE"
    MOSTLY_COMPLETE = "MOSTLY_COMPLETE"
    PARTIALLY_COMPLETE = "PARTIALLY_COMPLETE"
    INSUFFICIENT = "INSUFFICIENT"
    UNKNOWN = "UNKNOWN"


class CaseMaturityIndicatorType(str, Enum):
    """Explainable dimensions used by deterministic maturity scoring."""

    EVIDENCE_AVAILABLE = "EVIDENCE_AVAILABLE"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    OFFICIAL_DOCUMENTS = "OFFICIAL_DOCUMENTS"
    MISSING_DOCUMENTS = "MISSING_DOCUMENTS"
    DECLARATIVE_EVIDENCE = "DECLARATIVE_EVIDENCE"
    DOCUMENT_VERSIONS = "DOCUMENT_VERSIONS"
    ADMINISTRATIVE_VALIDATION = "ADMINISTRATIVE_VALIDATION"
    TIMELINE_COHERENCE = "TIMELINE_COHERENCE"
    DOCUMENTARY_COHERENCE = "DOCUMENTARY_COHERENCE"


class CaseMaturityIndicatorState(str, Enum):
    """Qualitative indicator state without percentage."""

    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    CONFLICTED = "CONFLICTED"
    REQUIRES_VALIDATION = "REQUIRES_VALIDATION"
    COHERENT = "COHERENT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class PotentialRightsReportView(str, Enum):
    """Employee and expert projections of the same analysis."""

    EMPLOYEE_VIEW = "EMPLOYEE_VIEW"
    EXPERT_VIEW = "EXPERT_VIEW"


@dataclass(frozen=True)
class PotentialRightReason:
    """Short factual reason for examining a generic scheme."""

    reason_id: str
    description: str
    provenance: str


@dataclass(frozen=True)
class PotentialRightEvidence:
    """Opaque evidence reference supporting further examination."""

    evidence_id: str
    source_type: str
    status: str
    provenance: str


@dataclass(frozen=True)
class PotentialRightGap:
    """Missing information associated with a potential scheme."""

    gap_id: str
    description: str
    required_document: str | None = None


@dataclass(frozen=True)
class MissingRequirement:
    """Unmet case-file requirement, without adverse legal inference."""

    requirement_id: str
    category: PotentialRightCategory | None
    description: str
    source: str


@dataclass(frozen=True)
class OfficialValidation:
    """Validation to request from a competent authority."""

    validation_id: str
    category: PotentialRightCategory | None
    authority: str
    reason: str
    completed: bool = False


@dataclass(frozen=True)
class PotentialRightRecommendation:
    """Prudent next step that does not assert a right."""

    recommendation_id: str
    category: PotentialRightCategory | None
    action: str
    organization: str | None = None


@dataclass(frozen=True)
class PotentialRight:
    """Generic scheme to examine, explicitly not an attributed entitlement."""

    potential_right_id: str
    category: PotentialRightCategory
    status: PotentialRightStatus
    priority: PotentialRightPriority
    reasons: tuple[PotentialRightReason, ...]
    evidence: tuple[PotentialRightEvidence, ...] = ()
    gaps: tuple[PotentialRightGap, ...] = ()
    official_validation_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CaseMaturityIndicator:
    """One explainable observation about documentary case quality."""

    indicator_type: CaseMaturityIndicatorType
    state: CaseMaturityIndicatorState
    explanation: str
    provenance: str


@dataclass(frozen=True)
class CaseMaturity:
    """Deterministic qualitative maturity of the case file only."""

    level: CaseMaturityLevel
    indicators: tuple[CaseMaturityIndicator, ...]
    justification: tuple[str, ...]


@dataclass(frozen=True)
class PotentialRightsContext:
    """Input context reusing the outputs of LOT 2 through LOT 5."""

    context_id: str
    timeline: CareerTimeline
    evidence_bundle: EvidenceBundle
    knowledge_context: KnowledgeContext
    reasoning_report: ReasoningReport
    synthetic_only: bool = True


@dataclass(frozen=True)
class PotentialRightsSummary:
    """Compact count-free summary of the analysis status."""

    maturity_level: CaseMaturityLevel
    categories_to_examine: tuple[PotentialRightCategory, ...]
    has_missing_requirements: bool
    official_validation_required: bool
    has_conflicts: bool


@dataclass(frozen=True)
class PotentialRightsReport:
    """Audience-safe report that never attributes an entitlement."""

    view: PotentialRightsReportView
    summary: PotentialRightsSummary
    schemes_to_examine: tuple[str, ...]
    reasons: tuple[str, ...]
    documents_to_provide: tuple[str, ...]
    organizations: tuple[str, ...]
    next_steps: tuple[str, ...]
    maturity: CaseMaturity
    warnings: tuple[str, ...]
    rules: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    document_versions: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    detailed_indicators: tuple[str, ...] = ()
    score_justification: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class PotentialRightsAnalysis:
    """Complete deterministic result before audience-specific projection."""

    potential_rights: tuple[PotentialRight, ...]
    maturity: CaseMaturity
    missing_requirements: tuple[MissingRequirement, ...]
    official_validations: tuple[OfficialValidation, ...]
    recommendations: tuple[PotentialRightRecommendation, ...]
