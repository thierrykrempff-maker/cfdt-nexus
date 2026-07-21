"""Read-only structural validation for synthetic career timelines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .career_timeline_models import CareerConflict, CareerEvent, CareerTimeline, EvidenceLevel


@dataclass(frozen=True)
class TimelineValidationIssue:
    """One detected anomaly that requires human review."""

    issue_type: str
    event_refs: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class TimelineValidationResult:
    """Immutable collection of validation findings."""

    valid: bool
    issues: tuple[TimelineValidationIssue, ...]
    conflicts: tuple[CareerConflict, ...]


def _parsed(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)


class CareerTimelineValidator:
    """Detect structural anomalies without modifying or completing events."""

    def validate(self, timeline: CareerTimeline) -> TimelineValidationResult:
        issues: list[TimelineValidationIssue] = []
        conflicts: list[CareerConflict] = []
        parsed: dict[str, tuple[date | None, date | None]] = {}

        for event in timeline.events:
            try:
                start, end = _parsed(event.start_date), _parsed(event.end_date)
                parsed[event.event_id] = (start, end)
            except ValueError:
                issues.append(self._issue("INVALID_DATE", (event.event_id,), "Invalid ISO calendar date."))
                continue
            if start is not None and end is not None and end < start:
                issues.append(self._issue("IMPOSSIBLE_PERIOD", (event.event_id,), "End date precedes start date."))
            if not event.source or event.evidence_level is EvidenceLevel.UNKNOWN:
                issues.append(self._issue("INSUFFICIENT_EVIDENCE", (event.event_id,), "Source or evidence level is insufficient."))

        self._detect_duplicates(timeline.events, issues)
        self._detect_overlaps(timeline.events, parsed, issues)
        self._detect_source_conflicts(timeline.events, issues, conflicts)
        return TimelineValidationResult(not issues, tuple(issues), tuple(conflicts))

    @staticmethod
    def _issue(issue_type: str, refs: tuple[str, ...], description: str) -> TimelineValidationIssue:
        return TimelineValidationIssue(issue_type, refs, description)

    def _detect_duplicates(
        self, events: tuple[CareerEvent, ...], issues: list[TimelineValidationIssue]
    ) -> None:
        seen_ids: set[str] = set()
        seen_facts: dict[tuple[object, ...], str] = {}
        for event in events:
            if event.event_id in seen_ids:
                issues.append(self._issue("DUPLICATE", (event.event_id,), "Duplicate event identifier."))
            seen_ids.add(event.event_id)
            signature = (event.start_date, event.end_date, event.event_type, event.description, event.source)
            previous = seen_facts.get(signature)
            if previous is not None:
                issues.append(self._issue("DUPLICATE", (previous, event.event_id), "Duplicate career fact."))
            else:
                seen_facts[signature] = event.event_id

    def _detect_overlaps(
        self,
        events: tuple[CareerEvent, ...],
        parsed: dict[str, tuple[date | None, date | None]],
        issues: list[TimelineValidationIssue],
    ) -> None:
        for index, left in enumerate(events):
            left_dates = parsed.get(left.event_id)
            if left_dates is None or None in left_dates:
                continue
            for right in events[index + 1 :]:
                right_dates = parsed.get(right.event_id)
                if (
                    right_dates is None
                    or None in right_dates
                    or left.event_type is not right.event_type
                    or left.source != right.source
                ):
                    continue
                left_start, left_end = left_dates
                right_start, right_end = right_dates
                if left_start <= right_end and right_start <= left_end:
                    issues.append(self._issue("OVERLAP", (left.event_id, right.event_id), "Comparable periods overlap."))

    def _detect_source_conflicts(
        self,
        events: tuple[CareerEvent, ...],
        issues: list[TimelineValidationIssue],
        conflicts: list[CareerConflict],
    ) -> None:
        for index, left in enumerate(events):
            for right in events[index + 1 :]:
                if (
                    left.event_type is right.event_type
                    and left.start_date == right.start_date
                    and left.end_date == right.end_date
                    and left.source != right.source
                    and left.description != right.description
                ):
                    refs = (left.event_id, right.event_id)
                    issues.append(self._issue("SOURCE_CONFLICT", refs, "Sources describe the same interval differently."))
                    conflicts.append(CareerConflict("conflict:" + ":".join(refs), "SOURCE_CONFLICT", refs, "Conflicting source declarations."))
