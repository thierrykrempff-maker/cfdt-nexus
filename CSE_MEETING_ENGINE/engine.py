"""Deterministic metadata-only CSE meeting preparation engine."""

from __future__ import annotations

from CSE_DECISION_TRACKER import (
    CSEDecisionTracker,
    DecisionTrackerQuery,
    TrackedCSEItem,
)
from CSE_KNOWLEDGE_ENGINE import (
    CSEKnowledgeEngine,
    CSEKnowledgeItem,
    CSEKnowledgeQuery,
    RecurringSubject,
)
from DOCUMENT_INTELLIGENCE_CENTER import (
    DocumentKind,
    DocumentNavigationService,
    NavigationDocument,
)

from .models import (
    MeetingAgendaItem,
    MeetingIndicators,
    MeetingPreparationDossier,
    MeetingPreparationQuery,
    PreparationDocumentReference,
)
from .policy import (
    AgendaPriority,
    agenda_sort_key,
    is_actionable_status,
    is_due_by,
    validate_meeting_metadata,
)


class CSEMeetingPreparationEngine:
    """Assemble a meeting dossier from existing metadata services."""

    def __init__(
        self,
        knowledge_engine: CSEKnowledgeEngine,
        decision_tracker: CSEDecisionTracker,
        navigation: DocumentNavigationService,
    ) -> None:
        self._knowledge_engine = knowledge_engine
        self._decision_tracker = decision_tracker
        self._navigation = navigation

    def open_decisions(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[TrackedCSEItem, ...]:
        return tuple(
            item
            for item in self._decision_tracker.detect_decisions(
                self._tracker_query(query)
            )
            if is_actionable_status(item.status)
        )

    def due_commitments(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[TrackedCSEItem, ...]:
        return tuple(
            item
            for item in self._decision_tracker.track_management_commitments(
                self._tracker_query(query)
            )
            if is_actionable_status(item.status)
            and is_due_by(item.due_date, query.meeting_date)
        )

    def open_elected_actions(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[TrackedCSEItem, ...]:
        return tuple(
            item
            for item in self._decision_tracker.track_elected_actions(
                self._tracker_query(query)
            )
            if is_actionable_status(item.status)
        )

    def ongoing_consultations(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[CSEKnowledgeItem, ...]:
        closed_statuses = {"CLOSED", "CANCELLED", "COMPLETED"}
        consultations = tuple(
            item
            for item in self._knowledge_engine.past_consultations(
                self._knowledge_query(query)
            )
            if item.status.upper() not in closed_statuses
        )
        for item in consultations:
            self._validate_knowledge_item(item)
        return consultations

    def recurring_subjects(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[RecurringSubject, ...]:
        subjects = self._knowledge_engine.recurring_subjects()
        for item in subjects:
            validate_meeting_metadata(item.label, "recurring_subject")
        if query.subject is None:
            return subjects
        matching_minutes = {
            item.meeting_document_id
            for item in self._knowledge_engine.find_minutes_by_subject(
                self._knowledge_query(query)
            )
        }
        return tuple(
            item
            for item in subjects
            if matching_minutes.intersection(item.meeting_document_ids)
        )

    def previous_minutes(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[PreparationDocumentReference, ...]:
        summaries = self._knowledge_engine.find_minutes_by_subject(
            self._knowledge_query(query)
        )
        references: list[PreparationDocumentReference] = []
        for summary in summaries:
            document = self._navigation.get_document(
                summary.meeting_document_id
            )
            if document is not None:
                references.append(self._reference(document))
        return tuple(
            sorted(
                references,
                key=lambda item: (
                    item.publication_date or "",
                    item.document_id,
                ),
            )
        )

    def related_agreements(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[PreparationDocumentReference, ...]:
        agreements: dict[str, PreparationDocumentReference] = {}
        for minutes in self.previous_minutes(query):
            result = self._navigation.agreements_for_minutes(
                minutes.document_id
            )
            for document in result.documents:
                if document.document_kind is not DocumentKind.AGREEMENT:
                    continue
                agreements[document.document_id] = self._reference(document)
        return tuple(agreements[key] for key in sorted(agreements))

    def prepare_agenda(
        self,
        query: MeetingPreparationQuery,
    ) -> tuple[MeetingAgendaItem, ...]:
        agreements = self.related_agreements(query)
        agreement_ids = tuple(item.document_id for item in agreements)
        items: list[MeetingAgendaItem] = []
        for decision in self.open_decisions(query):
            items.append(
                self._agenda_from_tracked(
                    decision,
                    category="OPEN_DECISION",
                    priority=AgendaPriority.REQUIRED_FOLLOW_UP,
                    reason_code="PREVIOUS_DECISION_NOT_CLOSED",
                    agreement_ids=agreement_ids,
                )
            )
        for commitment in self.due_commitments(query):
            items.append(
                self._agenda_from_tracked(
                    commitment,
                    category="DUE_MANAGEMENT_COMMITMENT",
                    priority=AgendaPriority.REQUIRED_FOLLOW_UP,
                    reason_code="COMMITMENT_DUE_BY_MEETING",
                    agreement_ids=agreement_ids,
                )
            )
        for action in self.open_elected_actions(query):
            items.append(
                self._agenda_from_tracked(
                    action,
                    category="OPEN_ELECTED_ACTION",
                    priority=AgendaPriority.HIGH,
                    reason_code="ELECTED_ACTION_NOT_CLOSED",
                    agreement_ids=agreement_ids,
                )
            )
        for consultation in self.ongoing_consultations(query):
            items.append(
                MeetingAgendaItem(
                    label=consultation.title,
                    category="ONGOING_CONSULTATION",
                    priority=AgendaPriority.HIGH,
                    reason_code="CONSULTATION_NOT_CLOSED",
                    due_date=None,
                    source_document_ids=(
                        consultation.document_id,
                        *consultation.meeting_document_ids,
                    ),
                    agreement_document_ids=agreement_ids,
                )
            )
        for subject in self.recurring_subjects(query):
            items.append(
                MeetingAgendaItem(
                    label=subject.label,
                    category="RECURRING_SUBJECT",
                    priority=AgendaPriority.NORMAL,
                    reason_code="SUBJECT_RECURS_IN_CSE_HISTORY",
                    due_date=None,
                    source_document_ids=subject.meeting_document_ids,
                    agreement_document_ids=agreement_ids,
                )
            )
        return tuple(
            sorted(
                items,
                key=lambda item: agenda_sort_key(
                    item.priority,
                    item.due_date,
                    item.label,
                    item.source_document_ids[0],
                ),
            )
        )

    def indicators(
        self,
        query: MeetingPreparationQuery,
    ) -> MeetingIndicators:
        previous = self.previous_minutes(query)
        agreements = self.related_agreements(query)
        decisions = self.open_decisions(query)
        commitments = self.due_commitments(query)
        actions = self.open_elected_actions(query)
        consultations = self.ongoing_consultations(query)
        recurring = self.recurring_subjects(query)
        agenda = self.prepare_agenda(query)
        return MeetingIndicators(
            previous_minutes_count=len(previous),
            related_agreement_count=len(agreements),
            open_decision_count=len(decisions),
            due_commitment_count=len(commitments),
            open_elected_action_count=len(actions),
            ongoing_consultation_count=len(consultations),
            recurring_subject_count=len(recurring),
            agenda_item_count=len(agenda),
        )

    def prepare_dossier(
        self,
        query: MeetingPreparationQuery,
    ) -> MeetingPreparationDossier:
        previous = self.previous_minutes(query)
        agreements = self.related_agreements(query)
        decisions = self.open_decisions(query)
        commitments = self.due_commitments(query)
        actions = self.open_elected_actions(query)
        consultations = self.ongoing_consultations(query)
        recurring = self.recurring_subjects(query)
        agenda = self.prepare_agenda(query)
        return MeetingPreparationDossier(
            query=query,
            agenda=agenda,
            open_decisions=decisions,
            due_commitments=commitments,
            open_elected_actions=actions,
            ongoing_consultations=consultations,
            recurring_subjects=recurring,
            previous_minutes=previous,
            related_agreements=agreements,
            indicators=MeetingIndicators(
                previous_minutes_count=len(previous),
                related_agreement_count=len(agreements),
                open_decision_count=len(decisions),
                due_commitment_count=len(commitments),
                open_elected_action_count=len(actions),
                ongoing_consultation_count=len(consultations),
                recurring_subject_count=len(recurring),
                agenda_item_count=len(agenda),
            ),
        )

    @staticmethod
    def _knowledge_query(
        query: MeetingPreparationQuery,
    ) -> CSEKnowledgeQuery:
        return CSEKnowledgeQuery(
            subject=query.subject,
            date_from=query.history_date_from,
            date_to=query.history_date_to,
            instance=query.instance,
        )

    @staticmethod
    def _tracker_query(
        query: MeetingPreparationQuery,
    ) -> DecisionTrackerQuery:
        return DecisionTrackerQuery(
            subject=query.subject,
            date_from=query.history_date_from,
            date_to=query.history_date_to,
            as_of_date=query.meeting_date,
            instance=query.instance,
        )

    @staticmethod
    def _reference(
        document: NavigationDocument,
    ) -> PreparationDocumentReference:
        return PreparationDocumentReference(
            document_id=document.document_id,
            title=document.title,
            document_kind=document.document_kind.value,
            publication_date=document.publication_date,
            family=document.family,
            status=document.status,
        )

    @staticmethod
    def _agenda_from_tracked(
        item: TrackedCSEItem,
        *,
        category: str,
        priority: AgendaPriority,
        reason_code: str,
        agreement_ids: tuple[str, ...],
    ) -> MeetingAgendaItem:
        return MeetingAgendaItem(
            label=item.title,
            category=category,
            priority=priority,
            reason_code=reason_code,
            due_date=item.due_date,
            source_document_ids=(
                item.document_id,
                *item.meeting_document_ids,
            ),
            agreement_document_ids=agreement_ids,
        )

    @staticmethod
    def _validate_knowledge_item(item: CSEKnowledgeItem) -> None:
        for field_name in (
            "title",
            "category",
            "status",
            "publication_date",
            "family",
        ):
            value = getattr(item, field_name)
            if value is not None:
                validate_meeting_metadata(value, field_name)
