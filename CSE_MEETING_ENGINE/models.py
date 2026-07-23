"""Immutable, serializable models for CSE meeting preparation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from DOCUMENT_INTELLIGENCE_CENTER.ingestion_models import is_pseudonymous_id

from CSE_DECISION_TRACKER import TrackedCSEItem
from CSE_KNOWLEDGE_ENGINE import CSEKnowledgeItem, RecurringSubject

from .policy import (
    AgendaPriority,
    parse_meeting_date,
    validate_meeting_metadata,
)


def _safe_ids(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    normalized = tuple(sorted(set(values)))
    if any(not is_pseudonymous_id(value) for value in normalized):
        raise ValueError(f"{field_name} must contain pseudonymized identifiers")
    return normalized


@dataclass(frozen=True, slots=True)
class MeetingPreparationQuery:
    """Explicit inputs for a deterministic meeting preparation."""

    meeting_date: str
    subject: str | None = None
    history_date_from: str | None = None
    history_date_to: str | None = None
    instance: str = "CSE"

    def __post_init__(self) -> None:
        parse_meeting_date(self.meeting_date, "meeting_date")
        for field_name in (
            "subject",
            "history_date_from",
            "history_date_to",
            "instance",
        ):
            value = getattr(self, field_name)
            if value is not None:
                validate_meeting_metadata(value, field_name)
        if self.history_date_from is not None:
            parse_meeting_date(self.history_date_from, "history_date_from")
        if self.history_date_to is not None:
            parse_meeting_date(self.history_date_to, "history_date_to")

    def to_dict(self) -> dict[str, str | None]:
        return {
            "history_date_from": self.history_date_from,
            "history_date_to": self.history_date_to,
            "instance": self.instance,
            "meeting_date": self.meeting_date,
            "subject": self.subject,
        }


@dataclass(frozen=True, slots=True)
class PreparationDocumentReference:
    """Safe metadata reference to a previous PV or related agreement."""

    document_id: str
    title: str
    document_kind: str
    publication_date: str | None
    family: str | None
    status: str

    def __post_init__(self) -> None:
        if not is_pseudonymous_id(self.document_id):
            raise ValueError("document_id must be pseudonymized")
        for field_name in (
            "title",
            "document_kind",
            "publication_date",
            "family",
            "status",
        ):
            value = getattr(self, field_name)
            if value is not None:
                validate_meeting_metadata(value, field_name)

    def to_dict(self) -> dict[str, str | None]:
        return {
            "document_id": self.document_id,
            "document_kind": self.document_kind,
            "family": self.family,
            "publication_date": self.publication_date,
            "status": self.status,
            "title": self.title,
        }


@dataclass(frozen=True, slots=True)
class MeetingAgendaItem:
    """One explainable agenda point derived from explicit metadata."""

    label: str
    category: str
    priority: AgendaPriority
    reason_code: str
    due_date: str | None
    source_document_ids: tuple[str, ...]
    agreement_document_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.priority, AgendaPriority):
            raise TypeError("priority must be an AgendaPriority")
        for field_name in ("label", "category", "reason_code", "due_date"):
            value = getattr(self, field_name)
            if value is not None:
                validate_meeting_metadata(value, field_name)
        if self.due_date is not None:
            parse_meeting_date(self.due_date, "due_date")
        object.__setattr__(
            self,
            "source_document_ids",
            _safe_ids(self.source_document_ids, "source_document_ids"),
        )
        object.__setattr__(
            self,
            "agreement_document_ids",
            _safe_ids(
                self.agreement_document_ids,
                "agreement_document_ids",
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "agreement_document_ids": list(self.agreement_document_ids),
            "category": self.category,
            "due_date": self.due_date,
            "label": self.label,
            "priority": self.priority.value,
            "reason_code": self.reason_code,
            "source_document_ids": list(self.source_document_ids),
        }


@dataclass(frozen=True, slots=True)
class MeetingIndicators:
    """Metadata-only counters for the prepared meeting."""

    previous_minutes_count: int
    related_agreement_count: int
    open_decision_count: int
    due_commitment_count: int
    open_elected_action_count: int
    ongoing_consultation_count: int
    recurring_subject_count: int
    agenda_item_count: int

    def __post_init__(self) -> None:
        values = (
            self.previous_minutes_count,
            self.related_agreement_count,
            self.open_decision_count,
            self.due_commitment_count,
            self.open_elected_action_count,
            self.ongoing_consultation_count,
            self.recurring_subject_count,
            self.agenda_item_count,
        )
        if any(value < 0 for value in values):
            raise ValueError("indicators cannot be negative")

    def to_dict(self) -> dict[str, int]:
        return {
            "agenda_item_count": self.agenda_item_count,
            "due_commitment_count": self.due_commitment_count,
            "ongoing_consultation_count": self.ongoing_consultation_count,
            "open_decision_count": self.open_decision_count,
            "open_elected_action_count": self.open_elected_action_count,
            "previous_minutes_count": self.previous_minutes_count,
            "recurring_subject_count": self.recurring_subject_count,
            "related_agreement_count": self.related_agreement_count,
        }


@dataclass(frozen=True, slots=True)
class MeetingPreparationDossier:
    """Complete metadata-only preparation dossier."""

    query: MeetingPreparationQuery
    agenda: tuple[MeetingAgendaItem, ...]
    open_decisions: tuple[TrackedCSEItem, ...]
    due_commitments: tuple[TrackedCSEItem, ...]
    open_elected_actions: tuple[TrackedCSEItem, ...]
    ongoing_consultations: tuple[CSEKnowledgeItem, ...]
    recurring_subjects: tuple[RecurringSubject, ...]
    previous_minutes: tuple[PreparationDocumentReference, ...]
    related_agreements: tuple[PreparationDocumentReference, ...]
    indicators: MeetingIndicators

    def to_dict(self) -> dict[str, Any]:
        return {
            "agenda": [item.to_dict() for item in self.agenda],
            "due_commitments": [
                item.to_dict() for item in self.due_commitments
            ],
            "indicators": self.indicators.to_dict(),
            "ongoing_consultations": [
                item.to_dict() for item in self.ongoing_consultations
            ],
            "open_decisions": [
                item.to_dict() for item in self.open_decisions
            ],
            "open_elected_actions": [
                item.to_dict() for item in self.open_elected_actions
            ],
            "previous_minutes": [
                item.to_dict() for item in self.previous_minutes
            ],
            "query": self.query.to_dict(),
            "recurring_subjects": [
                item.to_dict() for item in self.recurring_subjects
            ],
            "related_agreements": [
                item.to_dict() for item in self.related_agreements
            ],
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
