"""Deterministic CSE knowledge engine over the public navigation API."""

from __future__ import annotations

from collections import defaultdict

from DOCUMENT_INTELLIGENCE_CENTER import (
    DocumentKind,
    DocumentNavigationService,
    NavigationDocument,
    NavigationQuery,
    RelationKind,
)

from .models import (
    AgendaItem,
    CSEKnowledgeItem,
    CSEKnowledgeQuery,
    CSEKnowledgeReport,
    CSEMeetingSummary,
    RecurringSubject,
)
from .policy import (
    CONSULTATION_NATURE,
    DECISION_NATURE,
    MANAGEMENT_COMMITMENT_NATURE,
    OPEN_STATUSES,
    matches_subject,
    normalize_label,
    subject_labels,
)


class CSEKnowledgeEngine:
    """Read-only metadata reasoning for CSE history and preparation."""

    _FACT_RELATIONS = (
        RelationKind.DECIDES_ON,
        RelationKind.DISCUSSES,
        RelationKind.IMPLEMENTS,
        RelationKind.REFERENCES,
    )

    def __init__(self, navigation: DocumentNavigationService) -> None:
        self._navigation = navigation

    def find_minutes_by_subject(
        self,
        query: CSEKnowledgeQuery,
    ) -> tuple[CSEMeetingSummary, ...]:
        meetings = self._minutes(query)
        if query.subject is not None:
            meetings = tuple(
                meeting
                for meeting in meetings
                if self._meeting_matches(meeting, query.subject)
            )
        return tuple(self._summarize(meeting) for meeting in meetings)

    def find_decisions(
        self,
        query: CSEKnowledgeQuery | None = None,
    ) -> tuple[CSEKnowledgeItem, ...]:
        return self._linked_items(
            query,
            category=DECISION_NATURE,
            relation_kinds=(RelationKind.DECIDES_ON,),
        )

    def track_management_commitments(
        self,
        query: CSEKnowledgeQuery | None = None,
    ) -> tuple[CSEKnowledgeItem, ...]:
        return self._linked_items(
            query,
            category=MANAGEMENT_COMMITMENT_NATURE,
            relation_kinds=(
                RelationKind.DISCUSSES,
                RelationKind.IMPLEMENTS,
            ),
        )

    def past_consultations(
        self,
        query: CSEKnowledgeQuery | None = None,
    ) -> tuple[CSEKnowledgeItem, ...]:
        return self._linked_items(
            query,
            category=CONSULTATION_NATURE,
            relation_kinds=(
                RelationKind.DISCUSSES,
                RelationKind.REFERENCES,
            ),
        )

    def recurring_subjects(
        self,
        *,
        minimum_occurrences: int = 2,
    ) -> tuple[RecurringSubject, ...]:
        if minimum_occurrences < 2:
            raise ValueError("minimum_occurrences must be at least 2")
        occurrences: dict[str, set[str]] = defaultdict(set)
        labels: dict[str, str] = {}
        for meeting in self._minutes(CSEKnowledgeQuery()):
            related = self._related_documents(meeting.document_id)
            for document in (meeting, *related):
                for label in subject_labels(document):
                    key = normalize_label(label)
                    labels.setdefault(key, label)
                    occurrences[key].add(meeting.document_id)
        return tuple(
            RecurringSubject(
                label=labels[key],
                occurrence_count=len(occurrences[key]),
                meeting_document_ids=tuple(occurrences[key]),
            )
            for key in sorted(occurrences)
            if len(occurrences[key]) >= minimum_occurrences
        )

    def prepare_agenda(
        self,
        *,
        minimum_occurrences: int = 2,
    ) -> tuple[AgendaItem, ...]:
        items: list[AgendaItem] = []
        for recurring in self.recurring_subjects(
            minimum_occurrences=minimum_occurrences
        ):
            items.append(
                AgendaItem(
                    label=recurring.label,
                    category="RECURRING_SUBJECT",
                    priority=2,
                    reason="Sujet récurrent dans l'historique CSE",
                    source_document_ids=recurring.meeting_document_ids,
                )
            )
        for commitment in self.track_management_commitments():
            if commitment.status.upper() not in OPEN_STATUSES:
                continue
            items.append(
                AgendaItem(
                    label=commitment.title,
                    category="OPEN_MANAGEMENT_COMMITMENT",
                    priority=1,
                    reason="Engagement de la direction restant à suivre",
                    source_document_ids=(
                        commitment.document_id,
                        *commitment.meeting_document_ids,
                    ),
                )
            )
        return tuple(
            sorted(
                items,
                key=lambda item: (
                    item.priority,
                    normalize_label(item.label),
                    item.source_document_ids,
                ),
            )
        )

    def summarize_meetings(
        self,
        query: CSEKnowledgeQuery | None = None,
    ) -> tuple[CSEMeetingSummary, ...]:
        effective_query = query or CSEKnowledgeQuery()
        return self.find_minutes_by_subject(effective_query)

    def build_report(self, query: CSEKnowledgeQuery) -> CSEKnowledgeReport:
        return CSEKnowledgeReport(
            query=query,
            meetings=self.find_minutes_by_subject(query),
            decisions=self.find_decisions(query),
            commitments=self.track_management_commitments(query),
            consultations=self.past_consultations(query),
            recurring_subjects=self.recurring_subjects(),
            agenda_items=self.prepare_agenda(),
        )

    def _minutes(
        self,
        query: CSEKnowledgeQuery,
    ) -> tuple[NavigationDocument, ...]:
        result = self._navigation.search(
            NavigationQuery(
                document_kind=DocumentKind.CSE_MINUTES,
                date_from=query.date_from,
                date_to=query.date_to,
                instance=query.instance,
            )
        )
        return tuple(
            sorted(
                result.documents,
                key=lambda item: (
                    item.publication_date or "",
                    item.document_id,
                ),
            )
        )

    def _meeting_matches(
        self,
        meeting: NavigationDocument,
        subject: str,
    ) -> bool:
        if matches_subject(meeting, subject):
            return True
        return any(
            matches_subject(document, subject)
            for document in self._related_documents(meeting.document_id)
        )

    def _related_documents(
        self,
        meeting_document_id: str,
        relation_kinds: tuple[RelationKind, ...] | None = None,
    ) -> tuple[NavigationDocument, ...]:
        result = self._navigation.outgoing(
            meeting_document_id,
            relation_kinds or self._FACT_RELATIONS,
        )
        return tuple(
            item
            for item in result.documents
            if item.document_id != meeting_document_id
        )

    def _linked_items(
        self,
        query: CSEKnowledgeQuery | None,
        *,
        category: str,
        relation_kinds: tuple[RelationKind, ...],
    ) -> tuple[CSEKnowledgeItem, ...]:
        effective_query = query or CSEKnowledgeQuery()
        meetings = self._minutes(effective_query)
        if effective_query.subject is not None:
            meetings = tuple(
                meeting
                for meeting in meetings
                if self._meeting_matches(meeting, effective_query.subject)
            )
        documents: dict[str, NavigationDocument] = {}
        meeting_ids: dict[str, set[str]] = defaultdict(set)
        for meeting in meetings:
            for document in self._related_documents(
                meeting.document_id,
                relation_kinds,
            ):
                if (document.nature or "").upper() != category:
                    continue
                documents[document.document_id] = document
                meeting_ids[document.document_id].add(meeting.document_id)
        return tuple(
            self._item(documents[document_id], category, meeting_ids[document_id])
            for document_id in sorted(documents)
        )

    def _summarize(self, meeting: NavigationDocument) -> CSEMeetingSummary:
        related = self._related_documents(meeting.document_id)
        natures = tuple((item.nature or "").upper() for item in related)
        return CSEMeetingSummary(
            meeting_document_id=meeting.document_id,
            title=meeting.title,
            publication_date=meeting.publication_date,
            instance=meeting.instance or "CSE",
            decision_count=natures.count(DECISION_NATURE),
            commitment_count=natures.count(MANAGEMENT_COMMITMENT_NATURE),
            consultation_count=natures.count(CONSULTATION_NATURE),
            related_document_ids=tuple(item.document_id for item in related),
        )

    @staticmethod
    def _item(
        document: NavigationDocument,
        category: str,
        meeting_document_ids: set[str],
    ) -> CSEKnowledgeItem:
        return CSEKnowledgeItem(
            document_id=document.document_id,
            title=document.title,
            category=category,
            status=document.status,
            publication_date=document.publication_date,
            family=document.family,
            meeting_document_ids=tuple(meeting_document_ids),
        )
