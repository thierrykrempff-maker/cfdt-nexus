"""Neutral, pseudonymous technical identifiers used by Nexus Core."""

from __future__ import annotations

from dataclasses import dataclass
import re


_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_LONG_DIGITS = re.compile(r"\d{10,}")
_IBAN = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{10,30}$")
_RUNTIME_HASHED_IDENTIFIER = re.compile(
    r"^runtime-(?P<namespace>[a-z][a-z0-9-]*)-(?P<digest>[0-9a-f]{24})$"
)


def _is_runtime_hashed_identifier(candidate: str) -> bool:
    """Recognize the explicit pseudonymous SHA-256 format used by the Runtime."""

    match = _RUNTIME_HASHED_IDENTIFIER.fullmatch(candidate)
    if match is None:
        return False
    namespace = re.sub(r"[\s-]", "", match.group("namespace")).upper()
    digest = match.group("digest")
    return (
        not _LONG_DIGITS.search(namespace)
        and not _IBAN.fullmatch(namespace)
        and any(character in "abcdef" for character in digest)
    )


def _validate_identifier(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("technical identifier must be a non-empty string")
    candidate = value.strip()
    compact = re.sub(r"[\s-]", "", candidate).upper()
    if _EMAIL.fullmatch(candidate) or _IBAN.fullmatch(compact):
        raise ValueError("technical identifier must not contain direct personal data")
    if _LONG_DIGITS.search(compact) and not _is_runtime_hashed_identifier(candidate):
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
