"""Value-free models for active retirement privacy decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PrivacyStatus(str, Enum):
    SAFE = "SAFE"
    SAFE_WITH_WARNINGS = "SAFE_WITH_WARNINGS"
    BLOCKED = "BLOCKED"
    INSPECTION_ERROR = "INSPECTION_ERROR"


class PrivacyCategory(str, Enum):
    NIR = "NIR"
    IBAN = "IBAN"
    RIB = "RIB"
    INTERNAL_IDENTIFIER = "INTERNAL_IDENTIFIER"
    DIRECT_IDENTITY = "DIRECT_IDENTITY"
    PERSONAL_EMAIL = "PERSONAL_EMAIL"
    PERSONAL_PHONE = "PERSONAL_PHONE"
    POSTAL_ADDRESS = "POSTAL_ADDRESS"
    REAL_DOCUMENT = "REAL_DOCUMENT"
    REAL_SOURCE = "REAL_SOURCE"
    MISSING_PROVENANCE = "MISSING_PROVENANCE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSPECTION = "INSPECTION"


class PrivacySeverity(str, Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class PrivacyFinding:
    """One value-free finding; raw and masked excerpts are prohibited."""

    category: PrivacyCategory
    severity: PrivacySeverity
    field_path: str
    code: str
    explanation: str
    required_action: str


@dataclass(frozen=True)
class PrivacyInspection:
    """Deterministic inspection result containing no inspected values."""

    status: PrivacyStatus
    findings: tuple[PrivacyFinding, ...] = ()

    @property
    def safe(self) -> bool:
        return self.status in {PrivacyStatus.SAFE, PrivacyStatus.SAFE_WITH_WARNINGS}


__all__ = (
    "PrivacyCategory",
    "PrivacyFinding",
    "PrivacyInspection",
    "PrivacySeverity",
    "PrivacyStatus",
)
