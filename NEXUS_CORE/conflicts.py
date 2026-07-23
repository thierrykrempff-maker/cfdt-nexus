"""Conflict records that preserve alternatives without choosing one."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .identifiers import ConflictId, EntityId, EvidenceId
from .periods import Period


class ConflictStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


class ConflictReason(str, Enum):
    VALUE_MISMATCH = "value_mismatch"
    PERIOD_MISMATCH = "period_mismatch"
    SOURCE_MISMATCH = "source_mismatch"
    DUPLICATE = "duplicate"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ConflictResolutionReference:
    resolution_id: EntityId


@dataclass(frozen=True, slots=True)
class EvidenceConflict:
    conflict_id: ConflictId
    evidence_references: tuple[EvidenceId, ...]
    reason: ConflictReason
    period: Period | None
    status: ConflictStatus = ConflictStatus.OPEN
    resolution_reference: ConflictResolutionReference | None = None
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if len(self.evidence_references) < 2:
            raise ValueError("a conflict must preserve at least two evidence references")
