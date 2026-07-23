"""Deterministic policy for metadata-only CSE meeting preparation."""

from __future__ import annotations

from datetime import date
from enum import Enum
import re

from DOCUMENT_INTELLIGENCE_CENTER.ingestion_models import validate_safe_metadata

from CSE_DECISION_TRACKER import TrackingStatus
from CSE_KNOWLEDGE_ENGINE.policy import normalize_label


class AgendaPriority(str, Enum):
    """Operational priority, without implicit legal qualification."""

    REQUIRED_FOLLOW_UP = "REQUIRED_FOLLOW_UP"
    HIGH = "HIGH"
    NORMAL = "NORMAL"


_LOCAL_PATH = re.compile(r"(?i)(?:[a-z]:\\|/(?:home|users|tmp|var)/)")


def validate_meeting_metadata(value: str, field_name: str) -> str:
    """Reject unsafe values at the meeting-engine boundary."""

    normalized = validate_safe_metadata(value, field_name)
    if _LOCAL_PATH.search(normalized):
        raise ValueError(f"{field_name}: forbidden local path")
    return normalized


def parse_meeting_date(value: str, field_name: str) -> date:
    """Validate a required ISO date."""

    validate_meeting_metadata(value, field_name)
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field_name} must be an ISO date") from error


def is_due_by(due_date: str | None, meeting_date: str) -> bool:
    """Return whether an explicit deadline occurs by the meeting date."""

    if due_date is None:
        return False
    return parse_meeting_date(due_date, "due_date") <= parse_meeting_date(
        meeting_date,
        "meeting_date",
    )


def is_actionable_status(status: TrackingStatus) -> bool:
    """Keep only lifecycle states that still require operational follow-up."""

    return status not in (TrackingStatus.CLOSED, TrackingStatus.CANCELLED)


def agenda_sort_key(
    priority: AgendaPriority,
    due_date: str | None,
    label: str,
    stable_identifier: str,
) -> tuple[int, str, str, str]:
    rank = {
        AgendaPriority.REQUIRED_FOLLOW_UP: 0,
        AgendaPriority.HIGH: 1,
        AgendaPriority.NORMAL: 2,
    }
    return (
        rank[priority],
        due_date or "9999-12-31",
        normalize_label(label),
        stable_identifier,
    )
