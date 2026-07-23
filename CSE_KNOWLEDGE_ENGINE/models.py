"""Immutable, serializable metadata-only CSE knowledge models."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from DOCUMENT_INTELLIGENCE_CENTER import (
    is_pseudonymous_id,
    validate_safe_metadata,
)


def _validate_ids(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    normalized = tuple(sorted(set(values)))
    if any(not is_pseudonymous_id(value) for value in normalized):
        raise ValueError(f"{field_name} must contain pseudonymized identifiers")
    return normalized


@dataclass(frozen=True, slots=True)
class CSEKnowledgeQuery:
    """Deterministic filters used to retrieve CSE meeting metadata."""

    subject: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    instance: str = "CSE"

    def __post_init__(self) -> None:
        for field_name in ("subject", "date_from", "date_to", "instance"):
            value = getattr(self, field_name)
            if value is not None:
                validate_safe_metadata(value, field_name)

    def to_dict(self) -> dict[str, str | None]:
        return {
            "date_from": self.date_from,
            "date_to": self.date_to,
            "instance": self.instance,
            "subject": self.subject,
        }


@dataclass(frozen=True, slots=True)
class CSEKnowledgeItem:
    """A safe metadata projection for a CSE fact linked to meetings."""

    document_id: str
    title: str
    category: str
    status: str
    publication_date: str | None
    family: str | None
    meeting_document_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not is_pseudonymous_id(self.document_id):
            raise ValueError("document_id must be pseudonymized")
        for field_name in (
            "title",
            "category",
            "status",
            "publication_date",
            "family",
        ):
            value = getattr(self, field_name)
            if value is not None:
                validate_safe_metadata(value, field_name)
        object.__setattr__(
            self,
            "meeting_document_ids",
            _validate_ids(self.meeting_document_ids, "meeting_document_ids"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "document_id": self.document_id,
            "family": self.family,
            "meeting_document_ids": list(self.meeting_document_ids),
            "publication_date": self.publication_date,
            "status": self.status,
            "title": self.title,
        }


@dataclass(frozen=True, slots=True)
class RecurringSubject:
    """A controlled subject observed in more than one CSE meeting."""

    label: str
    occurrence_count: int
    meeting_document_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        validate_safe_metadata(self.label, "label")
        object.__setattr__(
            self,
            "meeting_document_ids",
            _validate_ids(self.meeting_document_ids, "meeting_document_ids"),
        )
        if self.occurrence_count != len(self.meeting_document_ids):
            raise ValueError("occurrence_count must match unique meetings")

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "meeting_document_ids": list(self.meeting_document_ids),
            "occurrence_count": self.occurrence_count,
        }


@dataclass(frozen=True, slots=True)
class AgendaItem:
    """An explainable agenda suggestion derived from historical metadata."""

    label: str
    category: str
    priority: int
    reason: str
    source_document_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in ("label", "category", "reason"):
            validate_safe_metadata(getattr(self, field_name), field_name)
        if not 1 <= self.priority <= 3:
            raise ValueError("priority must be between 1 and 3")
        object.__setattr__(
            self,
            "source_document_ids",
            _validate_ids(self.source_document_ids, "source_document_ids"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "label": self.label,
            "priority": self.priority,
            "reason": self.reason,
            "source_document_ids": list(self.source_document_ids),
        }


@dataclass(frozen=True, slots=True)
class CSEMeetingSummary:
    """Metadata-only synthesis of one CSE meeting."""

    meeting_document_id: str
    title: str
    publication_date: str | None
    instance: str
    decision_count: int
    commitment_count: int
    consultation_count: int
    related_document_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not is_pseudonymous_id(self.meeting_document_id):
            raise ValueError("meeting_document_id must be pseudonymized")
        for field_name in ("title", "publication_date", "instance"):
            value = getattr(self, field_name)
            if value is not None:
                validate_safe_metadata(value, field_name)
        object.__setattr__(
            self,
            "related_document_ids",
            _validate_ids(self.related_document_ids, "related_document_ids"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "commitment_count": self.commitment_count,
            "consultation_count": self.consultation_count,
            "decision_count": self.decision_count,
            "instance": self.instance,
            "meeting_document_id": self.meeting_document_id,
            "publication_date": self.publication_date,
            "related_document_ids": list(self.related_document_ids),
            "title": self.title,
        }


@dataclass(frozen=True, slots=True)
class CSEKnowledgeReport:
    """Complete deterministic CSE knowledge response."""

    query: CSEKnowledgeQuery
    meetings: tuple[CSEMeetingSummary, ...]
    decisions: tuple[CSEKnowledgeItem, ...]
    commitments: tuple[CSEKnowledgeItem, ...]
    consultations: tuple[CSEKnowledgeItem, ...]
    recurring_subjects: tuple[RecurringSubject, ...]
    agenda_items: tuple[AgendaItem, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "agenda_items": [item.to_dict() for item in self.agenda_items],
            "commitments": [item.to_dict() for item in self.commitments],
            "consultations": [item.to_dict() for item in self.consultations],
            "decisions": [item.to_dict() for item in self.decisions],
            "meetings": [item.to_dict() for item in self.meetings],
            "query": self.query.to_dict(),
            "recurring_subjects": [
                item.to_dict() for item in self.recurring_subjects
            ],
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
