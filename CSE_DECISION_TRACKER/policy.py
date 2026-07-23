"""Deterministic status and recurrence policy for CSE tracking."""

from __future__ import annotations

from datetime import date
from enum import Enum
import re

from DOCUMENT_INTELLIGENCE_CENTER.ingestion_models import validate_safe_metadata

from CSE_KNOWLEDGE_ENGINE.policy import normalize_label


class TrackingStatus(str, Enum):
    """Normalized lifecycle used by every tracked CSE item."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


DECISION_CATEGORY = "DECISION"
MANAGEMENT_COMMITMENT_CATEGORY = "MANAGEMENT_COMMITMENT"
ELECTED_ACTION_CATEGORY = "ELECTED_ACTION"

_STATUS_ALIASES = {
    "ACTIVE": TrackingStatus.OPEN,
    "A_FAIRE": TrackingStatus.OPEN,
    "OPEN": TrackingStatus.OPEN,
    "OUVERT": TrackingStatus.OPEN,
    "IN_PROGRESS": TrackingStatus.IN_PROGRESS,
    "EN_COURS": TrackingStatus.IN_PROGRESS,
    "PENDING": TrackingStatus.IN_PROGRESS,
    "CLOSED": TrackingStatus.CLOSED,
    "CLOTURE": TrackingStatus.CLOSED,
    "COMPLETED": TrackingStatus.CLOSED,
    "DONE": TrackingStatus.CLOSED,
    "CANCELLED": TrackingStatus.CANCELLED,
    "ANNULE": TrackingStatus.CANCELLED,
    "UNKNOWN": TrackingStatus.UNKNOWN,
}
_LOCAL_PATH = re.compile(
    r"(?i)(?:[a-z]:\\|/(?:home|users|tmp|var)/)"
)


def validate_tracker_metadata(value: str, field_name: str) -> str:
    """Apply the shared checks plus a case-insensitive local-path guard."""

    normalized = validate_safe_metadata(value, field_name)
    if _LOCAL_PATH.search(normalized):
        raise ValueError(f"{field_name}: forbidden local path")
    return normalized


def normalize_status(value: str) -> TrackingStatus:
    """Map an explicit documentary status without inferring a lifecycle."""

    validate_tracker_metadata(value, "status")
    key = normalize_label(value).replace(" ", "_").upper()
    return _STATUS_ALIASES.get(key, TrackingStatus.UNKNOWN)


def parse_iso_date(value: str | None, field_name: str) -> date | None:
    """Validate and parse an optional ISO date."""

    if value is None:
        return None
    validate_tracker_metadata(value, field_name)
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field_name} must be an ISO date") from error


def is_overdue(
    *,
    due_date: str | None,
    as_of_date: str | None,
    status: TrackingStatus,
) -> bool:
    """Evaluate delay only from explicit dates supplied to the engine."""

    due = parse_iso_date(due_date, "due_date")
    reference = parse_iso_date(as_of_date, "as_of_date")
    if due is None or reference is None:
        return False
    if status in (TrackingStatus.CLOSED, TrackingStatus.CANCELLED):
        return False
    return due < reference


def recurrence_key(title: str, family: str | None) -> str:
    """Build an explainable recurrence key from controlled metadata."""

    return normalize_label(family or title)
