"""Immutable and serializable metadata-only decision tracking models."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from DOCUMENT_INTELLIGENCE_CENTER.ingestion_models import is_pseudonymous_id

from .policy import (
    TrackingStatus,
    parse_iso_date,
    validate_tracker_metadata,
)


def _safe_ids(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    normalized = tuple(sorted(set(values)))
    if any(not is_pseudonymous_id(value) for value in normalized):
        raise ValueError(f"{field_name} must contain pseudonymized identifiers")
    return normalized


@dataclass(frozen=True, slots=True)
class DecisionTrackerQuery:
    """Filters and deterministic reference date for one tracking report."""

    subject: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    as_of_date: str | None = None
    instance: str = "CSE"

    def __post_init__(self) -> None:
        for field_name in (
            "subject",
            "date_from",
            "date_to",
            "as_of_date",
            "instance",
        ):
            value = getattr(self, field_name)
            if value is not None:
                validate_tracker_metadata(value, field_name)
        parse_iso_date(self.date_from, "date_from")
        parse_iso_date(self.date_to, "date_to")
        parse_iso_date(self.as_of_date, "as_of_date")

    def to_dict(self) -> dict[str, str | None]:
        return {
            "as_of_date": self.as_of_date,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "instance": self.instance,
            "subject": self.subject,
        }


@dataclass(frozen=True, slots=True)
class TrackedCSEItem:
    """One decision, management commitment or elected-member action."""

    document_id: str
    category: str
    title: str
    status: TrackingStatus
    publication_date: str | None
    due_date: str | None
    family: str | None
    meeting_document_ids: tuple[str, ...]
    follow_up_document_ids: tuple[str, ...] = ()
    overdue: bool = False

    def __post_init__(self) -> None:
        if not is_pseudonymous_id(self.document_id):
            raise ValueError("document_id must be pseudonymized")
        if not isinstance(self.status, TrackingStatus):
            raise TypeError("status must be a TrackingStatus")
        for field_name in (
            "category",
            "title",
            "publication_date",
            "due_date",
            "family",
        ):
            value = getattr(self, field_name)
            if value is not None:
                validate_tracker_metadata(value, field_name)
        parse_iso_date(self.publication_date, "publication_date")
        parse_iso_date(self.due_date, "due_date")
        object.__setattr__(
            self,
            "meeting_document_ids",
            _safe_ids(self.meeting_document_ids, "meeting_document_ids"),
        )
        object.__setattr__(
            self,
            "follow_up_document_ids",
            _safe_ids(self.follow_up_document_ids, "follow_up_document_ids"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "document_id": self.document_id,
            "due_date": self.due_date,
            "family": self.family,
            "follow_up_document_ids": list(self.follow_up_document_ids),
            "meeting_document_ids": list(self.meeting_document_ids),
            "overdue": self.overdue,
            "publication_date": self.publication_date,
            "status": self.status.value,
            "title": self.title,
        }


@dataclass(frozen=True, slots=True)
class RecurringDecision:
    """A deterministic group of decisions sharing controlled metadata."""

    label: str
    decision_document_ids: tuple[str, ...]
    meeting_document_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        validate_tracker_metadata(self.label, "label")
        object.__setattr__(
            self,
            "decision_document_ids",
            _safe_ids(self.decision_document_ids, "decision_document_ids"),
        )
        object.__setattr__(
            self,
            "meeting_document_ids",
            _safe_ids(self.meeting_document_ids, "meeting_document_ids"),
        )
        if len(self.decision_document_ids) < 2:
            raise ValueError("a recurring decision requires at least two decisions")

    @property
    def occurrence_count(self) -> int:
        return len(self.decision_document_ids)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_document_ids": list(self.decision_document_ids),
            "label": self.label,
            "meeting_document_ids": list(self.meeting_document_ids),
            "occurrence_count": self.occurrence_count,
        }


@dataclass(frozen=True, slots=True)
class TrackingStatistics:
    """Aggregate metadata-only indicators for the tracking table."""

    decision_count: int
    commitment_count: int
    elected_action_count: int
    open_count: int
    in_progress_count: int
    closed_count: int
    cancelled_count: int
    unknown_count: int
    overdue_action_count: int
    decisions_without_follow_up_count: int
    recurring_decision_group_count: int
    closure_rate: float

    def __post_init__(self) -> None:
        numeric_values = (
            self.decision_count,
            self.commitment_count,
            self.elected_action_count,
            self.open_count,
            self.in_progress_count,
            self.closed_count,
            self.cancelled_count,
            self.unknown_count,
            self.overdue_action_count,
            self.decisions_without_follow_up_count,
            self.recurring_decision_group_count,
        )
        if any(value < 0 for value in numeric_values):
            raise ValueError("statistics cannot be negative")
        if not 0.0 <= self.closure_rate <= 100.0:
            raise ValueError("closure_rate must be between 0 and 100")

    def to_dict(self) -> dict[str, int | float]:
        return {
            "cancelled_count": self.cancelled_count,
            "closed_count": self.closed_count,
            "closure_rate": self.closure_rate,
            "commitment_count": self.commitment_count,
            "decision_count": self.decision_count,
            "decisions_without_follow_up_count": (
                self.decisions_without_follow_up_count
            ),
            "elected_action_count": self.elected_action_count,
            "in_progress_count": self.in_progress_count,
            "open_count": self.open_count,
            "overdue_action_count": self.overdue_action_count,
            "recurring_decision_group_count": (
                self.recurring_decision_group_count
            ),
            "unknown_count": self.unknown_count,
        }


@dataclass(frozen=True, slots=True)
class FollowUpAgendaSection:
    """Metadata-only agenda section for previous decisions."""

    title: str
    items: tuple[TrackedCSEItem, ...]

    def __post_init__(self) -> None:
        validate_tracker_metadata(self.title, "title")

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "title": self.title,
        }


@dataclass(frozen=True, slots=True)
class DecisionTrackingReport:
    """Complete deterministic tracker result."""

    query: DecisionTrackerQuery
    decisions: tuple[TrackedCSEItem, ...]
    management_commitments: tuple[TrackedCSEItem, ...]
    elected_actions: tuple[TrackedCSEItem, ...]
    decisions_without_follow_up: tuple[str, ...]
    recurring_decisions: tuple[RecurringDecision, ...]
    agenda_section: FollowUpAgendaSection
    statistics: TrackingStatistics

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "decisions_without_follow_up",
            _safe_ids(
                self.decisions_without_follow_up,
                "decisions_without_follow_up",
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "agenda_section": self.agenda_section.to_dict(),
            "decisions": [item.to_dict() for item in self.decisions],
            "decisions_without_follow_up": list(
                self.decisions_without_follow_up
            ),
            "elected_actions": [
                item.to_dict() for item in self.elected_actions
            ],
            "management_commitments": [
                item.to_dict() for item in self.management_commitments
            ],
            "query": self.query.to_dict(),
            "recurring_decisions": [
                item.to_dict() for item in self.recurring_decisions
            ],
            "statistics": self.statistics.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
