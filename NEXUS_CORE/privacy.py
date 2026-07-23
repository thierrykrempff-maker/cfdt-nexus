"""Privacy labels and safe metadata primitives for Nexus Core."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class ConfidentialityLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    HIGHLY_CONFIDENTIAL = "highly_confidential"
    RESTRICTED = "restricted"


class DataSensitivity(str, Enum):
    NON_SENSITIVE = "non_sensitive"
    PERSONAL = "personal"
    SENSITIVE = "sensitive"
    SECRET = "secret"


class RedactionStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    REDACTED = "redacted"
    OMITTED = "omitted"


MetadataScalar = str | int | float | bool | date | datetime | None


@dataclass(frozen=True, slots=True)
class MetadataEntry:
    """A typed metadata item whose value is deliberately hidden from repr."""

    key: str
    value: MetadataScalar = field(repr=False)
    sensitivity: DataSensitivity = DataSensitivity.NON_SENSITIVE
    redaction_status: RedactionStatus = RedactionStatus.NOT_REQUIRED

    def __post_init__(self) -> None:
        if not self.key or not self.key.replace("_", "").isalnum():
            raise ValueError("metadata key must be a neutral technical name")


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """A diagnostic that cannot carry inspected values or free-form messages."""

    code: str
    category: str
    severity: str
    technical_reference: str | None = None

    def __post_init__(self) -> None:
        for value in (self.code, self.category, self.severity):
            if not value or not value.replace("_", "").isalnum():
                raise ValueError("diagnostic fields must be stable technical codes")
