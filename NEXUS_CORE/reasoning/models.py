"""Immutable, domain-neutral models for the Nexus reasoning pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..entities import EntityReference
from ..identifiers import EntityId, EvidenceId
from ..periods import Period
from ..privacy import Diagnostic
from ..provenance import Provenance
from ..quality import ConfidenceScore, EvidenceQuality, ValidationStatus
from ..values import EvidenceValueType


@dataclass(frozen=True, slots=True)
class FactType:
    """An extensible technical code supplied by an Evidence producer."""

    code: str

    def __post_init__(self) -> None:
        if not self.code or not self.code.replace("_", "").isalnum():
            raise ValueError("fact type must be a stable technical code")


@dataclass(frozen=True, slots=True)
class Fact:
    fact_id: EntityId
    source_evidence: EvidenceId
    subject_reference: EntityReference
    fact_type: FactType
    value: EvidenceValueType = field(repr=False)
    period: Period | None
    provenance: Provenance
    confidence: ConfidenceScore
    quality: EvidenceQuality
    validation_status: ValidationStatus
    schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class FactCollection:
    facts: tuple[Fact, ...] = ()
    schema_version: str = "1.0"

    def find(self, fact_id: EntityId) -> Fact | None:
        return next((fact for fact in self.facts if fact.fact_id == fact_id), None)


@dataclass(frozen=True, slots=True)
class FactCorrelation:
    correlation_id: EntityId
    subject_reference: EntityReference
    fact_type: FactType
    fact_references: tuple[EntityId, ...]
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if len(self.fact_references) < 2:
            raise ValueError("a correlation requires at least two facts")


class CorroborationStrength(str, Enum):
    TWO_DISTINCT_SOURCES = "two_distinct_sources"
    THREE_DISTINCT_SOURCES = "three_distinct_sources"
    MULTIPLE_DISTINCT_SOURCES = "multiple_distinct_sources"


@dataclass(frozen=True, slots=True)
class Corroboration:
    corroboration_id: EntityId
    fact_references: tuple[EntityId, ...]
    source_references: tuple[EntityId, ...]
    strength: CorroborationStrength
    period: Period | None
    schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class ConflictExplanation:
    code: str
    category: str
    fact_references: tuple[EntityId, ...]

    def __post_init__(self) -> None:
        for value in (self.code, self.category):
            if not value or not value.replace("_", "").isalnum():
                raise ValueError("conflict explanation must use technical codes")


@dataclass(frozen=True, slots=True)
class ReasoningConflict:
    conflict_id: EntityId
    fact_references: tuple[EntityId, ...]
    explanation: ConflictExplanation
    period: Period | None
    arbitrated: bool = False
    selected_fact: EntityId | None = None
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if len(self.fact_references) < 2:
            raise ValueError("a reasoning conflict requires at least two facts")
        if self.arbitrated or self.selected_fact is not None:
            raise ValueError("Core reasoning conflicts must never be arbitrated")


class MissingEvidenceReason(str, Enum):
    REQUIRED_FACT_ABSENT = "required_fact_absent"
    REQUIRED_PERIOD_NOT_COVERED = "required_period_not_covered"


@dataclass(frozen=True, slots=True)
class MissingEvidence:
    missing_id: EntityId
    subject_reference: EntityReference
    expected_fact_type: FactType
    reason: MissingEvidenceReason
    required_period: Period | None = None
    blocks_reasoning: bool = True
    schema_version: str = "1.0"


class ReasoningConfidence(str, Enum):
    INSUFFICIENT = "insufficient"
    LIMITED = "limited"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class ConfidenceAssessment:
    level: ReasoningConfidence
    technical_score: ConfidenceScore
    fact_count: int
    validated_fact_count: int
    conflict_count: int
    missing_evidence_count: int
    basis_codes: tuple[str, ...]
    schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class ReasoningStep:
    sequence: int
    code: str
    input_references: tuple[EntityId, ...] = ()
    output_references: tuple[EntityId, ...] = ()

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("reasoning step sequence starts at one")
        if not self.code or not self.code.replace("_", "").isalnum():
            raise ValueError("reasoning step must use a technical code")


@dataclass(frozen=True, slots=True)
class ReasoningReport:
    report_id: EntityId
    facts: FactCollection
    correlations: tuple[FactCorrelation, ...]
    corroborations: tuple[Corroboration, ...]
    conflicts: tuple[ReasoningConflict, ...]
    missing_evidence: tuple[MissingEvidence, ...]
    confidence: ConfidenceAssessment
    steps: tuple[ReasoningStep, ...]
    diagnostics: tuple[Diagnostic, ...]
    created_at: datetime
    schema_version: str = "1.0"
