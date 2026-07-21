"""Neutral immutable results for Kelio referential resolution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class KelioResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    RESOLVED_WITH_WARNINGS = "RESOLVED_WITH_WARNINGS"
    UNKNOWN = "UNKNOWN"
    INCOMPATIBLE = "INCOMPATIBLE"
    LOOKUP_ERROR = "LOOKUP_ERROR"


@dataclass(frozen=True)
class KelioCounterMetadata:
    """Technical metadata projected from the shared payroll referential."""

    referential_id: str
    canonical_counter_id: str
    category: str
    source_type: str
    resolution_status: KelioResolutionStatus
    evidence_kind: str
    synthetic_only: bool
    calculation_allowed: bool
    provenance: str


@dataclass(frozen=True)
class KelioCounterResolution:
    """Value-free resolution result; raw counter readings are never copied."""

    requested_counter_id: str
    status: KelioResolutionStatus
    metadata: KelioCounterMetadata | None = None
    warnings: tuple[str, ...] = ()
    code: str = "KELIO_REFERENTIAL_RESOLVED"

    @property
    def usable(self) -> bool:
        return self.status in {
            KelioResolutionStatus.RESOLVED,
            KelioResolutionStatus.RESOLVED_WITH_WARNINGS,
        }


__all__ = (
    "KelioCounterMetadata",
    "KelioCounterResolution",
    "KelioResolutionStatus",
)
