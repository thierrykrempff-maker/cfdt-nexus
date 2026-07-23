"""Public protocol for metadata-only CSE knowledge consumers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import (
    AgendaItem,
    CSEKnowledgeItem,
    CSEKnowledgeQuery,
    CSEKnowledgeReport,
    CSEMeetingSummary,
    RecurringSubject,
)


@runtime_checkable
class CSEKnowledgeAPI(Protocol):
    """Stable interface independent from Runtime and existing experts."""

    def find_minutes_by_subject(
        self,
        query: CSEKnowledgeQuery,
    ) -> tuple[CSEMeetingSummary, ...]: ...

    def find_decisions(
        self,
        query: CSEKnowledgeQuery | None = None,
    ) -> tuple[CSEKnowledgeItem, ...]: ...

    def track_management_commitments(
        self,
        query: CSEKnowledgeQuery | None = None,
    ) -> tuple[CSEKnowledgeItem, ...]: ...

    def past_consultations(
        self,
        query: CSEKnowledgeQuery | None = None,
    ) -> tuple[CSEKnowledgeItem, ...]: ...

    def recurring_subjects(
        self,
        *,
        minimum_occurrences: int = 2,
    ) -> tuple[RecurringSubject, ...]: ...

    def prepare_agenda(
        self,
        *,
        minimum_occurrences: int = 2,
    ) -> tuple[AgendaItem, ...]: ...

    def summarize_meetings(
        self,
        query: CSEKnowledgeQuery | None = None,
    ) -> tuple[CSEMeetingSummary, ...]: ...

    def build_report(self, query: CSEKnowledgeQuery) -> CSEKnowledgeReport: ...
