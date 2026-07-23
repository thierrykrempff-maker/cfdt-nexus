"""Neutral observations produced by domain engines."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .identifiers import EvidenceId, FindingId
from .periods import Period
from .privacy import MetadataEntry


class FindingType(str, Enum):
    OBSERVATION = "observation"
    ANOMALY = "anomaly"
    CONFLICT = "conflict"
    MISSING_DOCUMENT = "missing_document"
    MISSING_INFORMATION = "missing_information"
    POTENTIAL_RIGHT = "potential_right"
    RISK = "risk"
    CONSISTENCY_CHECK = "consistency_check"


class FindingSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


@dataclass(frozen=True, slots=True)
class Finding:
    finding_id: FindingId
    finding_type: FindingType
    severity: FindingSeverity
    status: FindingStatus
    code: str
    evidence_references: tuple[EvidenceId, ...] = ()
    period: Period | None = None
    metadata: tuple[MetadataEntry, ...] = ()
    schema_version: str = "1.0"
