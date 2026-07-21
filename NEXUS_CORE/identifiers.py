"""Neutral, pseudonymous technical identifiers used by Nexus Core."""

from __future__ import annotations

from dataclasses import dataclass
import re


_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_LONG_DIGITS = re.compile(r"\d{10,}")
_IBAN = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{10,30}$")


def _validate_identifier(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("technical identifier must be a non-empty string")
    candidate = value.strip()
    compact = re.sub(r"[\s-]", "", candidate).upper()
    if _EMAIL.fullmatch(candidate) or _IBAN.fullmatch(compact) or _LONG_DIGITS.search(compact):
        raise ValueError("technical identifier must not contain direct personal data")


@dataclass(frozen=True, slots=True)
class EntityId:
    value: str

    def __post_init__(self) -> None:
        _validate_identifier(self.value)

@dataclass(frozen=True, slots=True)
class CorrelationId:
    value: str

    def __post_init__(self) -> None:
        _validate_identifier(self.value)


@dataclass(frozen=True, slots=True)
class AnalysisId:
    value: str

    def __post_init__(self) -> None:
        _validate_identifier(self.value)


@dataclass(frozen=True, slots=True)
class DocumentId:
    value: str

    def __post_init__(self) -> None:
        _validate_identifier(self.value)


@dataclass(frozen=True, slots=True)
class EvidenceId:
    value: str

    def __post_init__(self) -> None:
        _validate_identifier(self.value)


@dataclass(frozen=True, slots=True)
class FindingId:
    value: str

    def __post_init__(self) -> None:
        _validate_identifier(self.value)


@dataclass(frozen=True, slots=True)
class RecommendationId:
    value: str

    def __post_init__(self) -> None:
        _validate_identifier(self.value)


@dataclass(frozen=True, slots=True)
class ConflictId:
    value: str

    def __post_init__(self) -> None:
        _validate_identifier(self.value)
