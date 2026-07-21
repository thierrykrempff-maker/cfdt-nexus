"""Immutable, domain-neutral models for documentary conflict resolution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..identifiers import EntityId, EvidenceId


def _technical_code(value: str, label: str) -> None:
    if not value or not value.replace("_", "").isalnum():
        raise ValueError(f"{label} must be a stable technical code")


class ResolutionCategory(str, Enum):
    NO_CONFLICT = "no_conflict"
    DOCUMENT_CONFLICT = "document_conflict"
    TEMPORAL_CONFLICT = "temporal_conflict"
    SOURCE_CONFLICT = "source_conflict"
    MISSING_EVIDENCE = "missing_evidence"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    PARTIAL_CORROBORATION = "partial_corroboration"
    STRONG_CORROBORATION = "strong_corroboration"
    MULTIPLE_HYPOTHESES = "multiple_hypotheses"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class ResolutionCandidate:
    """A documented situation, never a selected or preferred proof."""

    candidate_id: EntityId
    category: ResolutionCategory
    explanation_code: str
    evidence_references: tuple[EvidenceId, ...] = ()
    fact_references: tuple[EntityId, ...] = ()
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        _technical_code(self.explanation_code, "explanation code")


@dataclass(frozen=True, slots=True)
class ResolutionClassification:
    classification_id: EntityId
    category: ResolutionCategory
    explanation_code: str
    candidate_references: tuple[EntityId, ...]
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        _technical_code(self.explanation_code, "explanation code")


@dataclass(frozen=True, slots=True)
class ResolutionDiagnostic:
    """Safe diagnostic containing technical codes and references only."""

    code: str
    category: str
    severity: str
    technical_references: tuple[EntityId, ...] = ()
    expected_evidence_type: str | None = None
    usefulness_code: str | None = None
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        for value in (self.code, self.category, self.severity):
            _technical_code(value, "diagnostic field")
        for value in (self.expected_evidence_type, self.usefulness_code):
            if value is not None:
                _technical_code(value, "diagnostic detail")


@dataclass(frozen=True, slots=True)
class CoherenceAssessment:
    temporal: float
    documentary: float
    corroboration: float
    provenance: float
    completeness: float
    overall: float
    basis_codes: tuple[str, ...]
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        scores = (
            self.temporal,
            self.documentary,
            self.corroboration,
            self.provenance,
            self.completeness,
            self.overall,
        )
        if any(not 0.0 <= score <= 1.0 for score in scores):
            raise ValueError("coherence scores must be between zero and one")
        for code in self.basis_codes:
            _technical_code(code, "coherence basis code")


@dataclass(frozen=True, slots=True)
class ResolutionSummary:
    classification_count: int
    candidate_count: int
    diagnostic_count: int
    categories: tuple[ResolutionCategory, ...]
    coherence_score: float
    schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class ResolutionReport:
    report_id: EntityId
    source_reasoning_report: EntityId
    classifications: tuple[ResolutionClassification, ...]
    candidates: tuple[ResolutionCandidate, ...]
    diagnostics: tuple[ResolutionDiagnostic, ...]
    coherence: CoherenceAssessment
    summary: ResolutionSummary
    created_at: datetime
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if hasattr(self, "selected_evidence") or hasattr(self, "legal_conclusion"):
            raise ValueError("resolution reports cannot arbitrate or conclude")
