"""Typed, immutable contracts for issue-led legal research planning.

The contracts describe what should be researched.  They never execute a
connector, retrieve a document or state a legal conclusion.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class IssueCategory(str, Enum):
    DISCIPLINARY_PROCEDURE = "DISCIPLINARY_PROCEDURE"
    DISCIPLINARY_GROUNDS = "DISCIPLINARY_GROUNDS"
    PRIVATE_LIFE = "PRIVATE_LIFE"
    WORKING_TIME = "WORKING_TIME"
    BREAK_TIME = "BREAK_TIME"
    SHIFT_CHANGE = "SHIFT_CHANGE"
    CONTRACT_CHANGE = "CONTRACT_CHANGE"
    PAYROLL = "PAYROLL"
    HEALTH_SAFETY = "HEALTH_SAFETY"
    PPE = "PPE"
    ALCOHOL_TEST = "ALCOHOL_TEST"
    DATA_PROTECTION = "DATA_PROTECTION"
    EMPLOYEE_MONITORING = "EMPLOYEE_MONITORING"
    CSE_INFORMATION_CONSULTATION = "CSE_INFORMATION_CONSULTATION"
    CSSCT = "CSSCT"
    COLLECTIVE_AGREEMENT = "COLLECTIVE_AGREEMENT"
    CLASSIFICATION = "CLASSIFICATION"
    LEAVE = "LEAVE"
    INTERNAL_PROCEDURE = "INTERNAL_PROCEDURE"
    OTHER = "OTHER"


class SourceFamily(str, Enum):
    INEOS_AGREEMENT = "INEOS_AGREEMENT"
    INEOS_INTERNAL_RULE = "INEOS_INTERNAL_RULE"
    INEOS_PROCEDURE = "INEOS_PROCEDURE"
    CCNIC_IDCC_44 = "CCNIC_IDCC_44"
    LABOUR_CODE = "LABOUR_CODE"
    REGULATION = "REGULATION"
    CASE_LAW = "CASE_LAW"
    OFFICIAL_GUIDANCE = "OFFICIAL_GUIDANCE"
    CSE_MINUTES = "CSE_MINUTES"
    CSSCT_MINUTES = "CSSCT_MINUTES"
    INTERNAL_PRACTICE = "INTERNAL_PRACTICE"
    EMPLOYMENT_CONTRACT = "EMPLOYMENT_CONTRACT"
    OTHER = "OTHER"


class PlanningStatus(str, Enum):
    READY = "READY"
    PARTIALLY_READY = "PARTIALLY_READY"
    BLOCKED_BY_MISSING_FACTS = "BLOCKED_BY_MISSING_FACTS"
    NOT_RELEVANT = "NOT_RELEVANT"
    UNSUPPORTED = "UNSUPPORTED"
    CONDITIONAL_QUERY = "CONDITIONAL_QUERY"
    READY_AFTER_CLARIFICATION = "READY_AFTER_CLARIFICATION"


@dataclass(frozen=True, slots=True)
class LegalIssue:
    issue_id: str
    case_session_id: str
    title: str
    legal_question: str
    issue_category: IssueCategory
    associated_fact_ids: tuple[str, ...]
    blocking_fact_ids: tuple[str, ...]
    missing_information_ids: tuple[str, ...]
    urgency: str
    status: PlanningStatus
    confidence: str
    original_formulations: tuple[str, ...]
    created_from_rules: tuple[str, ...]
    requires_external_search: bool
    requires_internal_search: bool
    requires_cse_search: bool

    def __post_init__(self) -> None:
        required = (
            self.issue_id,
            self.case_session_id,
            self.title,
            self.legal_question,
            self.urgency,
            self.confidence,
        )
        if not all(value.strip() for value in required):
            raise ValueError("legal issue required fields must be non-empty")
        if not self.associated_fact_ids:
            raise ValueError("a legal issue must be linked to at least one fact")
        if not self.created_from_rules:
            raise ValueError("a legal issue must identify its deterministic rule")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["issue_category"] = self.issue_category.value
        payload["status"] = self.status.value
        return payload


@dataclass(frozen=True, slots=True)
class ResearchTarget:
    target_id: str
    issue_id: str
    source_family: SourceFamily
    source_priority: int
    purpose: str
    mandatory: bool
    expected_reference_type: str
    expected_evidence: str
    fallback_allowed: bool
    exclusion_reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.target_id,
                self.issue_id,
                self.purpose,
                self.expected_reference_type,
                self.expected_evidence,
            )
        ):
            raise ValueError("research target required fields must be non-empty")
        if not 1 <= self.source_priority <= 7:
            raise ValueError("source_priority must follow the 1..7 hierarchy")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["source_family"] = self.source_family.value
        return payload


@dataclass(frozen=True, slots=True)
class ResearchQuery:
    query_id: str
    issue_id: str
    target_id: str
    query_text: str
    concepts: tuple[str, ...]
    factual_scope: tuple[str, ...]
    temporal_scope: str
    establishment_scope: str
    employee_population_scope: str
    document_types: tuple[str, ...]
    expected_reference: str
    expected_excerpt: str
    negative_terms: tuple[str, ...]
    priority: int
    mandatory: bool
    reason: str
    status: PlanningStatus

    def __post_init__(self) -> None:
        required = (
            self.query_id,
            self.issue_id,
            self.target_id,
            self.query_text,
            self.temporal_scope,
            self.establishment_scope,
            self.employee_population_scope,
            self.expected_reference,
            self.expected_excerpt,
            self.reason,
        )
        if not all(value.strip() for value in required):
            raise ValueError("research query required fields must be non-empty")
        if not self.concepts or not self.factual_scope or not self.document_types:
            raise ValueError("research query scopes must be explicit")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


@dataclass(frozen=True, slots=True)
class ResearchExclusion:
    source_family: SourceFamily
    reason: str
    issue_id: str | None = None

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("research exclusion reason must be non-empty")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["source_family"] = self.source_family.value
        return payload


@dataclass(frozen=True, slots=True)
class ResearchPlan:
    plan_id: str
    case_session_id: str
    issues: tuple[LegalIssue, ...]
    targets: tuple[ResearchTarget, ...]
    queries: tuple[ResearchQuery, ...]
    blocked_queries: tuple[ResearchQuery, ...]
    exclusions: tuple[ResearchExclusion, ...]
    warnings: tuple[str, ...]
    completeness_status: PlanningStatus
    created_at: str | None
    version: str

    def __post_init__(self) -> None:
        if not self.plan_id.strip() or not self.case_session_id.strip():
            raise ValueError("research plan identity must be non-empty")
        if not self.version.strip():
            raise ValueError("research plan version must be non-empty")
        issue_ids = {issue.issue_id for issue in self.issues}
        target_ids = {target.target_id for target in self.targets}
        if len(issue_ids) != len(self.issues) or len(target_ids) != len(self.targets):
            raise ValueError("research plan identifiers must be unique")
        if any(target.issue_id not in issue_ids for target in self.targets):
            raise ValueError("every target must reference a plan issue")
        for query in (*self.queries, *self.blocked_queries):
            if query.issue_id not in issue_ids or query.target_id not in target_ids:
                raise ValueError("every query must reference a plan issue and target")

    def to_dict(self) -> dict[str, object]:
        return {
            "plan_id": self.plan_id,
            "case_session_id": self.case_session_id,
            "issues": [item.to_dict() for item in self.issues],
            "targets": [item.to_dict() for item in self.targets],
            "queries": [item.to_dict() for item in self.queries],
            "blocked_queries": [item.to_dict() for item in self.blocked_queries],
            "exclusions": [item.to_dict() for item in self.exclusions],
            "warnings": list(self.warnings),
            "completeness_status": self.completeness_status.value,
            "created_at": self.created_at,
            "version": self.version,
        }

    def to_public_dict(self) -> dict[str, object]:
        """Return a future-facing projection without technical identifiers."""

        target_by_issue: dict[str, list[ResearchTarget]] = {}
        for target in self.targets:
            target_by_issue.setdefault(target.issue_id, []).append(target)
        return {
            "title": "Ce que Nexus doit rechercher",
            "status": self.completeness_status.value,
            "questions": [
                {
                    "question": issue.legal_question,
                    "sources_planned": [
                        {
                            "family": target.source_family.value,
                            "purpose": target.purpose,
                            "mandatory": target.mandatory,
                        }
                        for target in target_by_issue.get(issue.issue_id, ())
                    ],
                    "state": issue.status.value,
                }
                for issue in self.issues
            ],
            "warnings": list(self.warnings),
        }


__all__ = (
    "IssueCategory",
    "LegalIssue",
    "PlanningStatus",
    "ResearchExclusion",
    "ResearchPlan",
    "ResearchQuery",
    "ResearchTarget",
    "SourceFamily",
)
