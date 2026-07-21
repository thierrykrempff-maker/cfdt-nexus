"""Immutable models for prudent, synthetic retirement-rule reasoning.

The models expose structured evaluations only.  They contain no legal
threshold, pension amount, retirement date, C2P computation or free-form
hidden reasoning.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .career_evidence_models import EvidenceBundle
from .career_timeline_models import CareerTimeline
from .document_knowledge_models import DocumentValidity, DocumentVersion, KnowledgeContext
from .document_rule_models import ApplicableRule


ReasoningValue = str | int | float | bool | tuple[str, ...] | None


class RuleConditionType(str, Enum):
    """Condition inputs accepted as already-declared facts."""

    AGE = "AGE"
    BIRTH_YEAR = "BIRTH_YEAR"
    CAREER_START_DATE = "CAREER_START_DATE"
    CAREER_DURATION = "CAREER_DURATION"
    INSURANCE_DURATION = "INSURANCE_DURATION"
    QUARTERS_RECORDED = "QUARTERS_RECORDED"
    NIGHT_WORK_DURATION = "NIGHT_WORK_DURATION"
    FIVE_SHIFT_DURATION = "FIVE_SHIFT_DURATION"
    SHIFT_WORK_DURATION = "SHIFT_WORK_DURATION"
    EXPOSURE_DURATION = "EXPOSURE_DURATION"
    C2P_POINTS = "C2P_POINTS"
    ATMP_STATUS = "ATMP_STATUS"
    PERMANENT_INCAPACITY_RATE = "PERMANENT_INCAPACITY_RATE"
    PART_TIME_STATUS = "PART_TIME_STATUS"
    INEOS_SENIORITY = "INEOS_SENIORITY"
    INEOS_POSITION = "INEOS_POSITION"
    INEOS_CLASSIFICATION = "INEOS_CLASSIFICATION"
    AGREEMENT_VALIDITY = "AGREEMENT_VALIDITY"
    DOCUMENT_REQUIRED = "DOCUMENT_REQUIRED"
    OFFICIAL_NOTIFICATION_REQUIRED = "OFFICIAL_NOTIFICATION_REQUIRED"
    OTHER_DECLARED_FACT = "OTHER_DECLARED_FACT"


class ConditionOperator(str, Enum):
    """Simple deterministic comparisons permitted by LOT 5."""

    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    GREATER_THAN = "GREATER_THAN"
    GREATER_OR_EQUAL = "GREATER_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_OR_EQUAL = "LESS_OR_EQUAL"
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    IN_PERIOD = "IN_PERIOD"
    EVENT_PRESENT = "EVENT_PRESENT"
    STATUS_KNOWN = "STATUS_KNOWN"


class ConditionEvaluationState(str, Enum):
    """Explicit, uncertainty-preserving evaluation states."""

    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    UNKNOWN = "UNKNOWN"
    PARTIALLY_SATISFIED = "PARTIALLY_SATISFIED"
    CONFLICTED = "CONFLICTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    REQUIRES_DOCUMENT = "REQUIRES_DOCUMENT"
    REQUIRES_OFFICIAL_VALIDATION = "REQUIRES_OFFICIAL_VALIDATION"


class GenericSchemeType(str, Enum):
    """Generic routes to examine, without their real legal rules."""

    LEGAL_RETIREMENT_AGE = "LEGAL_RETIREMENT_AGE"
    FULL_RATE_RETIREMENT = "FULL_RATE_RETIREMENT"
    LONG_CAREER = "LONG_CAREER"
    C2P_EARLY_RETIREMENT = "C2P_EARLY_RETIREMENT"
    PERMANENT_INCAPACITY_RETIREMENT = "PERMANENT_INCAPACITY_RETIREMENT"
    PROGRESSIVE_RETIREMENT = "PROGRESSIVE_RETIREMENT"
    DISABILITY_OR_UNFITNESS_ROUTE = "DISABILITY_OR_UNFITNESS_ROUTE"
    INEOS_END_OF_CAREER_MEASURE = "INEOS_END_OF_CAREER_MEASURE"
    INEOS_RETIREMENT_INDEMNITY = "INEOS_RETIREMENT_INDEMNITY"
    NIGHT_WORK_PREVENTION = "NIGHT_WORK_PREVENTION"
    WORKSTATION_ADAPTATION = "WORKSTATION_ADAPTATION"
    ATMP_RECOGNITION = "ATMP_RECOGNITION"
    CAREER_CORRECTION = "CAREER_CORRECTION"
    OTHER_SCHEME = "OTHER_SCHEME"


class ReasoningReportView(str, Enum):
    """Audience-specific projections of the same structured outcome."""

    EMPLOYEE_VIEW = "EMPLOYEE_VIEW"
    EXPERT_VIEW = "EXPERT_VIEW"


class ReasoningFactStatus(str, Enum):
    """Input fact state supplied by an upstream component."""

    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    CONFLICTED = "CONFLICTED"


@dataclass(frozen=True)
class ReasoningRequest:
    """Opaque request and generic schemes the worker asks to examine."""

    request_id: str
    question: str
    requested_schemes: tuple[GenericSchemeType, ...] = ()
    synthetic_only: bool = True


@dataclass(frozen=True)
class ReasoningFact:
    """Already-known input value; the engine never derives durations or points."""

    fact_key: str
    value: ReasoningValue
    status: ReasoningFactStatus
    provenance: str
    declarative: bool = False


@dataclass(frozen=True)
class RuleCondition:
    """One simple condition over an explicitly supplied fact or event."""

    condition_id: str
    condition_type: RuleConditionType
    operator: ConditionOperator
    fact_key: str
    expected_value: ReasoningValue = None
    provenance: str = ""


@dataclass(frozen=True)
class ReasoningRule:
    """Synthetic rule candidate linked to documentary metadata and provenance."""

    rule_id: str
    label: str
    scheme: GenericSchemeType
    conditions: tuple[RuleCondition, ...]
    provenance: str
    applicable_rule: ApplicableRule | None = None
    document_version: DocumentVersion | None = None
    collective_rule: bool = False
    official_validation_required: bool = True


@dataclass(frozen=True)
class ReasoningContext:
    """Pre-built local context combining LOT 2, LOT 3 and LOT 4 structures."""

    context_id: str
    request: ReasoningRequest
    timeline: CareerTimeline
    evidence_bundle: EvidenceBundle
    knowledge_context: KnowledgeContext
    facts: tuple[ReasoningFact, ...] = ()
    rules: tuple[ReasoningRule, ...] = ()


@dataclass(frozen=True)
class ConditionEvaluation:
    """Factual result for one simple condition."""

    condition_id: str
    state: ConditionEvaluationState
    observed_value: ReasoningValue
    provenance: str
    justification: str


@dataclass(frozen=True)
class ReasoningTrace:
    """Structured explainability record, never hidden chain-of-thought."""

    step_id: str
    rule_id: str | None
    condition_id: str | None
    input_used: str
    status: ConditionEvaluationState
    provenance: str
    justification: str


@dataclass(frozen=True)
class RuleEvaluation:
    """Combined condition states for one synthetic rule."""

    rule_id: str
    state: ConditionEvaluationState
    conditions: tuple[ConditionEvaluation, ...]
    trace: tuple[ReasoningTrace, ...]
    reasons: tuple[str, ...]
    provenance: str


@dataclass(frozen=True)
class ReasoningFinding:
    """Short factual finding derived from an explicit condition state."""

    finding_id: str
    rule_id: str
    description: str
    state: ConditionEvaluationState
    provenance: str


@dataclass(frozen=True)
class ReasoningGap:
    """Missing fact or documentary item that prevents stronger analysis."""

    gap_id: str
    rule_id: str
    condition_id: str
    description: str
    required_document: str | None = None


@dataclass(frozen=True)
class ReasoningConflict:
    """Preserved contradiction reported without automatic arbitration."""

    conflict_id: str
    rule_id: str
    condition_id: str
    description: str
    provenance: str


@dataclass(frozen=True)
class ReasoningWarning:
    """Prudential warning included in an explainable outcome."""

    warning_id: str
    message: str


@dataclass(frozen=True)
class ApplicableScheme:
    """Generic scheme to examine, not a confirmed individual entitlement."""

    scheme: GenericSchemeType
    source_rule_ids: tuple[str, ...]
    evaluation_state: ConditionEvaluationState
    reason: str


@dataclass(frozen=True)
class OfficialValidationRequirement:
    """Administrative validation explicitly required before any conclusion."""

    requirement_id: str
    scheme: GenericSchemeType
    authority: str
    reason: str
    satisfied: bool = False


@dataclass(frozen=True)
class ReasoningOutcome:
    """Complete local result preserving gaps, conflicts, provenance and trace."""

    evaluations: tuple[RuleEvaluation, ...]
    findings: tuple[ReasoningFinding, ...]
    gaps: tuple[ReasoningGap, ...]
    conflicts: tuple[ReasoningConflict, ...]
    schemes: tuple[ApplicableScheme, ...]
    official_validations: tuple[OfficialValidationRequirement, ...]
    warnings: tuple[ReasoningWarning, ...]
    trace: tuple[ReasoningTrace, ...]


@dataclass(frozen=True)
class ReasoningReport:
    """Audience-safe report without retirement date, amount or decision."""

    view: ReasoningReportView
    schemes_to_examine: tuple[str, ...]
    main_reasons: tuple[str, ...]
    confirmed_elements: tuple[str, ...]
    elements_to_verify: tuple[str, ...]
    missing_documents: tuple[str, ...]
    recommended_actions: tuple[str, ...]
    official_validation_required: bool
    warnings: tuple[str, ...]
    examined_rules: tuple[str, ...] = ()
    document_versions: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    trace: tuple[ReasoningTrace, ...] = ()
