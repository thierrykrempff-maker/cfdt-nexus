"""Technical confidence and evidence quality, independent from legal weight."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ConfidenceLevel(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"


@dataclass(frozen=True, slots=True)
class ConfidenceScore:
    value: float
    level: ConfidenceLevel

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("confidence score must be between 0 and 1")


class EvidenceQuality(str, Enum):
    UNKNOWN = "unknown"
    INCOMPLETE = "incomplete"
    CONSISTENT = "consistent"
    CORROBORATED = "corroborated"


class ValidationStatus(str, Enum):
    NOT_VALIDATED = "not_validated"
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
