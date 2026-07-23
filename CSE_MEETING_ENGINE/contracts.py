"""Public contract for deterministic CSE meeting preparation."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from CSE_DECISION_TRACKER import TrackedCSEItem
from CSE_KNOWLEDGE_ENGINE import CSEKnowledgeItem, RecurringSubject

from .models import (
    MeetingAgendaItem,
    MeetingIndicators,
    MeetingPreparationDossier,
    MeetingPreparationQuery,
    PreparationDocumentReference,
)


@runtime_checkable
class CSEMeetingPreparationAPI(Protocol):
    """Stable API independent from Runtime and existing experts."""

    def open_decisions(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[TrackedCSEItem, ...]: ...

    def due_commitments(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[TrackedCSEItem, ...]: ...

    def open_elected_actions(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[TrackedCSEItem, ...]: ...

    def ongoing_consultations(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[CSEKnowledgeItem, ...]: ...

    def recurring_subjects(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[RecurringSubject, ...]: ...

    def previous_minutes(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[PreparationDocumentReference, ...]: ...

    def related_agreements(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[PreparationDocumentReference, ...]: ...

    def prepare_agenda(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[MeetingAgendaItem, ...]: ...

    def indicators(
        self,
        query: MeetingPreparationQuery,
    ) -> MeetingIndicators: ...

    def prepare_dossier(
        self,
        query: MeetingPreparationQuery,
    ) -> MeetingPreparationDossier: ...
