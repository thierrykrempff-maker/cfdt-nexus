"""Immutable contracts for the canonical factual core.

These models describe only information supplied for the current case.  They
do not contain a legal qualification, a source-retrieval result or a proposed
argument.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class FactCategory(str, Enum):
    CERTAIN = "CERTAIN"
    ADMITTED = "ADMITTED"
    ALLEGED = "ALLEGED"
    DISPUTED = "DISPUTED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    CONTEXT = "CONTEXT"
    CONSEQUENCE = "CONSEQUENCE"
    MISSING_INFORMATION = "MISSING_INFORMATION"


class FactConfidence(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class FactualSource(str, Enum):
    USER_PROVIDED = "USER_PROVIDED"
    USER_ADMITTED = "USER_ADMITTED"
    USER_ALLEGED = "USER_ALLEGED"
    USER_DISPUTED = "USER_DISPUTED"
    USER_NOT_ESTABLISHED = "USER_NOT_ESTABLISHED"
    USER_CONTEXT = "USER_CONTEXT"
    USER_CONSEQUENCE = "USER_CONSEQUENCE"
    USER_MISSING_INFORMATION = "USER_MISSING_INFORMATION"


@dataclass(frozen=True, slots=True)
class FactFormulation:
    """One original formulation linked to its canonical fact."""

    formulation_id: str
    text: str
    factual_source: FactualSource
    semantic_duplicate_of: str | None = None

    def __post_init__(self) -> None:
        if not self.formulation_id.strip() or not self.text.strip():
            raise ValueError("fact formulation identifiers and text must be non-empty")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CanonicalFact:
    """A unique factual idea for one case or analysis session."""

    fact_id: str
    canonical_text: str
    category: FactCategory
    subject: str
    allegation_author: str | None
    factual_source: FactualSource
    confidence: FactConfidence
    original_formulations: tuple[FactFormulation, ...]
    origin_session_id: str

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.fact_id,
                self.canonical_text,
                self.subject,
                self.origin_session_id,
            )
        ):
            raise ValueError("canonical fact identity and text must be non-empty")
        if not self.original_formulations:
            raise ValueError("a canonical fact must retain an original formulation")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


__all__ = (
    "CanonicalFact",
    "FactCategory",
    "FactConfidence",
    "FactFormulation",
    "FactualSource",
)
