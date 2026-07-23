"""Metadata-only CSE decision and action tracking engine."""

from __future__ import annotations

from collections import defaultdict

from CSE_KNOWLEDGE_ENGINE import CSEKnowledgeEngine, CSEKnowledgeQuery
from DOCUMENT_INTELLIGENCE_CENTER import (
    DocumentNavigationService,
    NavigationDocument,
    RelationKind,
)

from .models import (
    DecisionTrackerQuery,
    DecisionTrackingReport,
    FollowUpAgendaSection,
    RecurringDecision,
    TrackedCSEItem,
    TrackingStatistics,
)
from .policy import (
    DECISION_CATEGORY,
    ELECTED_ACTION_CATEGORY,
    MANAGEMENT_COMMITMENT_CATEGORY,
    TrackingStatus,
    is_overdue,
    normalize_status,
    recurrence_key,
)


class CSEDecisionTracker:
    """Track explicit CSE facts without reading documentary content."""

    _MINUTES_FACT_RELATIONS = (
        RelationKind.DECIDES_ON,
        RelationKind.DISCUSSES,
        RelationKind.IMPLEMENTS,
        RelationKind.REFERENCES,
    )
    _FOLLOW_UP_RELATIONS = (
        RelationKind.APPLIES_TO,
        RelationKind.IMPLEMENTS,
        RelationKind.RELATED_TO,
    )

    def __init__(
        self,
        knowledge_engine: CSEKnowledgeEngine,
        navigation: DocumentNavigationService,
    ) -> None:
        self._knowledge_engine = knowledge_engine
        self._navigation = navigation

    def detect_decisions(
        self,
        query: DecisionTrackerQuery | None = None,
    ) -> tuple[TrackedCSEItem, ...]:
        effective = query or DecisionTrackerQuery()
        decisions = self._knowledge_engine.find_decisions(
            self._knowledge_query(effective)
        )
        return tuple(
            self._tracked_from_knowledge_item(
                item.document_id,
                item.title,
                DECISION_CATEGORY,
                item.status,
                item.publication_date,
                item.family,
                item.meeting_document_ids,
                effective,
            )
            for item in decisions
        )

    def track_management_commitments(
        self,
        query: DecisionTrackerQuery | None = None,
    ) -> tuple[TrackedCSEItem, ...]:
        effective = query or DecisionTrackerQuery()
        commitments = self._knowledge_engine.track_management_commitments(
            self._knowledge_query(effective)
        )
        return tuple(
            self._tracked_from_knowledge_item(
                item.document_id,
                item.title,
                MANAGEMENT_COMMITMENT_CATEGORY,
                item.status,
                item.publication_date,
                item.family,
                item.meeting_document_ids,
                effective,
            )
            for item in commitments
        )

    def track_elected_actions(
        self,
        query: DecisionTrackerQuery | None = None,
    ) -> tuple[TrackedCSEItem, ...]:
        effective = query or DecisionTrackerQuery()
        meeting_ids = tuple(
            item.meeting_document_id
            for item in self._knowledge_engine.find_minutes_by_subject(
                self._knowledge_query(effective)
            )
        )
        documents: dict[str, NavigationDocument] = {}
        meetings_by_action: dict[str, set[str]] = defaultdict(set)
        for meeting_id in meeting_ids:
            result = self._navigation.outgoing(
                meeting_id,
                self._MINUTES_FACT_RELATIONS,
            )
            for document in result.documents:
                if document.document_id == meeting_id:
                    continue
                if (document.nature or "").upper() != ELECTED_ACTION_CATEGORY:
                    continue
                documents[document.document_id] = document
                meetings_by_action[document.document_id].add(meeting_id)
        return tuple(
            self._tracked_document(
                documents[document_id],
                ELECTED_ACTION_CATEGORY,
                tuple(meetings_by_action[document_id]),
                effective,
            )
            for document_id in sorted(documents)
        )

    def decisions_without_follow_up(
        self,
        query: DecisionTrackerQuery | None = None,
    ) -> tuple[str, ...]:
        decisions = self.detect_decisions(query)
        return tuple(
            item.document_id
            for item in decisions
            if not item.follow_up_document_ids
        )

    def recurring_decisions(
        self,
        query: DecisionTrackerQuery | None = None,
    ) -> tuple[RecurringDecision, ...]:
        groups: dict[str, list[TrackedCSEItem]] = defaultdict(list)
        labels: dict[str, str] = {}
        for decision in self.detect_decisions(query):
            key = recurrence_key(decision.title, decision.family)
            labels.setdefault(key, decision.family or decision.title)
            groups[key].append(decision)
        recurring: list[RecurringDecision] = []
        for key in sorted(groups):
            items = groups[key]
            if len(items) < 2:
                continue
            recurring.append(
                RecurringDecision(
                    label=labels[key],
                    decision_document_ids=tuple(
                        item.document_id for item in items
                    ),
                    meeting_document_ids=tuple(
                        meeting_id
                        for item in items
                        for meeting_id in item.meeting_document_ids
                    ),
                )
            )
        return tuple(recurring)

    def prepare_follow_up_agenda(
        self,
        query: DecisionTrackerQuery | None = None,
    ) -> FollowUpAgendaSection:
        items = (
            *self.detect_decisions(query),
            *self.track_management_commitments(query),
            *self.track_elected_actions(query),
        )
        actionable = tuple(
            sorted(
                (
                    item
                    for item in items
                    if item.status
                    not in (TrackingStatus.CLOSED, TrackingStatus.CANCELLED)
                ),
                key=self._item_sort_key,
            )
        )
        return FollowUpAgendaSection(
            title="Suivi des décisions précédentes",
            items=actionable,
        )

    def statistics(
        self,
        query: DecisionTrackerQuery | None = None,
    ) -> TrackingStatistics:
        decisions = self.detect_decisions(query)
        commitments = self.track_management_commitments(query)
        actions = self.track_elected_actions(query)
        all_items = (*decisions, *commitments, *actions)
        status_counts = {
            status: sum(item.status is status for item in all_items)
            for status in TrackingStatus
        }
        decision_closed = sum(
            item.status is TrackingStatus.CLOSED for item in decisions
        )
        closure_rate = (
            round(100.0 * decision_closed / len(decisions), 2)
            if decisions
            else 0.0
        )
        return TrackingStatistics(
            decision_count=len(decisions),
            commitment_count=len(commitments),
            elected_action_count=len(actions),
            open_count=status_counts[TrackingStatus.OPEN],
            in_progress_count=status_counts[TrackingStatus.IN_PROGRESS],
            closed_count=status_counts[TrackingStatus.CLOSED],
            cancelled_count=status_counts[TrackingStatus.CANCELLED],
            unknown_count=status_counts[TrackingStatus.UNKNOWN],
            overdue_action_count=sum(item.overdue for item in actions),
            decisions_without_follow_up_count=len(
                self.decisions_without_follow_up(query)
            ),
            recurring_decision_group_count=len(
                self.recurring_decisions(query)
            ),
            closure_rate=closure_rate,
        )

    def build_report(
        self,
        query: DecisionTrackerQuery,
    ) -> DecisionTrackingReport:
        decisions = self.detect_decisions(query)
        commitments = self.track_management_commitments(query)
        actions = self.track_elected_actions(query)
        no_follow_up = tuple(
            item.document_id
            for item in decisions
            if not item.follow_up_document_ids
        )
        recurring = self._recurring_from_items(decisions)
        agenda_items = tuple(
            sorted(
                (
                    item
                    for item in (*decisions, *commitments, *actions)
                    if item.status
                    not in (TrackingStatus.CLOSED, TrackingStatus.CANCELLED)
                ),
                key=self._item_sort_key,
            )
        )
        statistics = self._statistics_from_items(
            decisions,
            commitments,
            actions,
            no_follow_up,
            recurring,
        )
        return DecisionTrackingReport(
            query=query,
            decisions=decisions,
            management_commitments=commitments,
            elected_actions=actions,
            decisions_without_follow_up=no_follow_up,
            recurring_decisions=recurring,
            agenda_section=FollowUpAgendaSection(
                title="Suivi des décisions précédentes",
                items=agenda_items,
            ),
            statistics=statistics,
        )

    def _tracked_from_knowledge_item(
        self,
        document_id: str,
        title: str,
        category: str,
        raw_status: str,
        publication_date: str | None,
        family: str | None,
        meeting_document_ids: tuple[str, ...],
        query: DecisionTrackerQuery,
    ) -> TrackedCSEItem:
        document = self._navigation.get_document(document_id)
        if document is None:
            raise ValueError("knowledge item is absent from navigation")
        return self._tracked(
            document=document,
            category=category,
            raw_status=raw_status,
            title=title,
            publication_date=publication_date,
            family=family,
            meeting_document_ids=meeting_document_ids,
            query=query,
        )

    def _tracked_document(
        self,
        document: NavigationDocument,
        category: str,
        meeting_document_ids: tuple[str, ...],
        query: DecisionTrackerQuery,
    ) -> TrackedCSEItem:
        return self._tracked(
            document=document,
            category=category,
            raw_status=document.status,
            title=document.title,
            publication_date=document.publication_date,
            family=document.family,
            meeting_document_ids=meeting_document_ids,
            query=query,
        )

    def _tracked(
        self,
        *,
        document: NavigationDocument,
        category: str,
        raw_status: str,
        title: str,
        publication_date: str | None,
        family: str | None,
        meeting_document_ids: tuple[str, ...],
        query: DecisionTrackerQuery,
    ) -> TrackedCSEItem:
        status = normalize_status(raw_status)
        follow_up_ids = self._follow_up_document_ids(document.document_id)
        return TrackedCSEItem(
            document_id=document.document_id,
            category=category,
            title=title,
            status=status,
            publication_date=publication_date,
            due_date=document.effective_to,
            family=family,
            meeting_document_ids=meeting_document_ids,
            follow_up_document_ids=follow_up_ids,
            overdue=is_overdue(
                due_date=document.effective_to,
                as_of_date=query.as_of_date,
                status=status,
            ),
        )

    def _follow_up_document_ids(self, document_id: str) -> tuple[str, ...]:
        result = self._navigation.outgoing(
            document_id,
            self._FOLLOW_UP_RELATIONS,
        )
        return tuple(
            item.document_id
            for item in result.documents
            if item.document_id != document_id
            and (item.nature or "").upper()
            in (MANAGEMENT_COMMITMENT_CATEGORY, ELECTED_ACTION_CATEGORY)
        )

    @staticmethod
    def _knowledge_query(query: DecisionTrackerQuery) -> CSEKnowledgeQuery:
        return CSEKnowledgeQuery(
            subject=query.subject,
            date_from=query.date_from,
            date_to=query.date_to,
            instance=query.instance,
        )

    @staticmethod
    def _item_sort_key(
        item: TrackedCSEItem,
    ) -> tuple[bool, str, str, str]:
        return (
            not item.overdue,
            item.due_date or "9999-12-31",
            recurrence_key(item.title, item.family),
            item.document_id,
        )

    @staticmethod
    def _recurring_from_items(
        decisions: tuple[TrackedCSEItem, ...],
    ) -> tuple[RecurringDecision, ...]:
        groups: dict[str, list[TrackedCSEItem]] = defaultdict(list)
        labels: dict[str, str] = {}
        for decision in decisions:
            key = recurrence_key(decision.title, decision.family)
            labels.setdefault(key, decision.family or decision.title)
            groups[key].append(decision)
        return tuple(
            RecurringDecision(
                label=labels[key],
                decision_document_ids=tuple(
                    item.document_id for item in groups[key]
                ),
                meeting_document_ids=tuple(
                    meeting_id
                    for item in groups[key]
                    for meeting_id in item.meeting_document_ids
                ),
            )
            for key in sorted(groups)
            if len(groups[key]) >= 2
        )

    @staticmethod
    def _statistics_from_items(
        decisions: tuple[TrackedCSEItem, ...],
        commitments: tuple[TrackedCSEItem, ...],
        actions: tuple[TrackedCSEItem, ...],
        no_follow_up: tuple[str, ...],
        recurring: tuple[RecurringDecision, ...],
    ) -> TrackingStatistics:
        all_items = (*decisions, *commitments, *actions)
        status_counts = {
            status: sum(item.status is status for item in all_items)
            for status in TrackingStatus
        }
        closed = sum(
            item.status is TrackingStatus.CLOSED for item in decisions
        )
        closure_rate = (
            round(100.0 * closed / len(decisions), 2)
            if decisions
            else 0.0
        )
        return TrackingStatistics(
            decision_count=len(decisions),
            commitment_count=len(commitments),
            elected_action_count=len(actions),
            open_count=status_counts[TrackingStatus.OPEN],
            in_progress_count=status_counts[TrackingStatus.IN_PROGRESS],
            closed_count=status_counts[TrackingStatus.CLOSED],
            cancelled_count=status_counts[TrackingStatus.CANCELLED],
            unknown_count=status_counts[TrackingStatus.UNKNOWN],
            overdue_action_count=sum(item.overdue for item in actions),
            decisions_without_follow_up_count=len(no_follow_up),
            recurring_decision_group_count=len(recurring),
            closure_rate=closure_rate,
        )
