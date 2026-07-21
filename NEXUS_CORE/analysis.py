"""Cross-domain requests and reference-only aggregate reports."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .conflicts import EvidenceConflict
from .entities import EntityReference
from .evidence import Evidence
from .findings import Finding
from .identifiers import (
    AnalysisId,
    ConflictId,
    CorrelationId,
    EntityId,
    EvidenceId,
    FindingId,
    RecommendationId,
)
from .periods import Period
from .privacy import Diagnostic, MetadataEntry
from .recommendations import Recommendation


class DomainSelection(str, Enum):
    LEGAL = "legal"
    PAYROLL = "payroll"
    RETIREMENT_PENIBILITY = "retirement_penibility"
    CSE = "cse"
    CSSCT = "cssct"
    SOCIAL_PROTECTION = "social_protection"
    CLASSIFICATION = "classification"
    DOCUMENT_KNOWLEDGE = "document_knowledge"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class AnalysisQuestion:
    question_code: str
    parameters: tuple[MetadataEntry, ...] = ()


@dataclass(frozen=True, slots=True)
class AnalysisScope:
    subjects: tuple[EntityReference, ...]
    period: Period | None = None


@dataclass(frozen=True, slots=True)
class AnalysisRequest:
    analysis_id: AnalysisId
    correlation_id: CorrelationId
    question: AnalysisQuestion
    scope: AnalysisScope
    domains: tuple[DomainSelection, ...]
    metadata: tuple[MetadataEntry, ...] = ()
    schema_version: str = "1.0"
    def __post_init__(self) -> None:
        if not self.domains:
            raise ValueError("at least one domain must be selected")
        if len(set(self.domains)) != len(self.domains):
            raise ValueError("domain selection must not contain duplicates")


@dataclass(frozen=True, slots=True)
class DomainAnalysisResult:
    domain: DomainSelection
    status: AnalysisStatus
    evidence: tuple[Evidence, ...] = ()
    findings: tuple[Finding, ...] = ()
    conflicts: tuple[EvidenceConflict, ...] = ()
    recommendations: tuple[Recommendation, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    metadata: tuple[MetadataEntry, ...] = ()
    schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class DomainResultReference:
    result_id: EntityId
    domain: DomainSelection
    status: AnalysisStatus


@dataclass(frozen=True, slots=True)
class AnalysisReport:
    analysis_id: AnalysisId
    status: AnalysisStatus
    evidence_references: tuple[EvidenceId, ...] = ()
    finding_references: tuple[FindingId, ...] = ()
    conflict_references: tuple[ConflictId, ...] = ()
    recommendation_references: tuple[RecommendationId, ...] = ()
    domain_results: tuple[DomainResultReference, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    metadata: tuple[MetadataEntry, ...] = ()
    schema_version: str = "1.0"
