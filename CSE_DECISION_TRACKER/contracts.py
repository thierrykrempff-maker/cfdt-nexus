"""Public protocol for the deterministic CSE decision tracker."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import (
    DecisionTrackerQuery,
    DecisionTrackingReport,
    FollowUpAgendaSection,
    RecurringDecision,
    TrackedCSEItem,
    TrackingStatistics,
)


@runtime_checkable
class CSEDecisionTrackerAPI(Protocol):
    """Stable API independent from Runtime and existing experts."""

    def detect_decisions(
        self,
        query: DecisionTrackerQuery | None = None,
    ) -> tuple[TrackedCSEItem, ...]: ...

    def track_management_commitments(
        self,
        query: DecisionTrackerQuery | None = None,
    ) -> tuple[TrackedCSEItem, ...]: ...

    def track_elected_actions(
        self,
        query: DecisionTrackerQuery | None = None,
    ) -> tuple[TrackedCSEItem, ...]: ...

    def decisions_without_follow_up(
        self,
        query: DecisionTrackerQuery | None = None,
    ) -> tuple[str, ...]: ...

    def recurring_decisions(
        self,
        query: DecisionTrackerQuery | None = None,
    ) -> tuple[RecurringDecision, ...]: ...

    def prepare_follow_up_agenda(
        self,
        query: DecisionTrackerQuery | None = None,
    ) -> FollowUpAgendaSection: ...

    def statistics(
        self,
        query: DecisionTrackerQuery | None = None,
    ) -> TrackingStatistics: ...

    def build_report(
        self,
        query: DecisionTrackerQuery,
    ) -> DecisionTrackingReport: ...
