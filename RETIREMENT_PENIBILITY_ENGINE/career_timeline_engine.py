"""Minimal immutable operations for the architecture-only career timeline."""

from __future__ import annotations

from dataclasses import replace

from .career_timeline_models import CareerEvent, CareerTimeline, TimelineReport
from .career_timeline_report import CareerTimelineReportBuilder
from .career_timeline_validator import CareerTimelineValidator, TimelineValidationResult
from .privacy_gate import RetirementPrivacyGate, require_privacy_gate


class CareerTimelineEngine:
    """Coordinate structural timeline operations without business calculation."""

    def __init__(
        self,
        validator: CareerTimelineValidator | None = None,
        report_builder: CareerTimelineReportBuilder | None = None,
        privacy_gate=RetirementPrivacyGate(),
    ) -> None:
        self._validator = validator or CareerTimelineValidator()
        self._report_builder = report_builder or CareerTimelineReportBuilder(self._validator)
        self._privacy_gate = privacy_gate

    def create_empty_timeline(
        self, timeline_id: str, employee_case_id: str | None = None
    ) -> CareerTimeline:
        """Create an empty synthetic timeline with opaque identifiers."""

        return CareerTimeline(timeline_id=timeline_id, employee_case_id=employee_case_id)

    def add_event(self, timeline: CareerTimeline, event: CareerEvent) -> CareerTimeline:
        """Return a new timeline containing the supplied event."""

        require_privacy_gate(self._privacy_gate).assert_safe((timeline, event))
        return replace(timeline, events=timeline.events + (event,))

    def remove_event(self, timeline: CareerTimeline, event_id: str) -> CareerTimeline:
        """Return a new timeline without events matching the opaque identifier."""

        require_privacy_gate(self._privacy_gate).assert_safe(timeline)
        return replace(timeline, events=tuple(event for event in timeline.events if event.event_id != event_id))

    def validate(self, timeline: CareerTimeline) -> TimelineValidationResult:
        """Report anomalies without correcting the timeline."""

        require_privacy_gate(self._privacy_gate).assert_safe(timeline)
        return self._validator.validate(timeline)

    def generate_report(self, timeline: CareerTimeline) -> TimelineReport:
        """Generate a structural report containing no pension estimate."""

        require_privacy_gate(self._privacy_gate).assert_safe(timeline)
        return self._report_builder.build(timeline)

    def merge_sources(
        self, timeline_id: str, timelines: tuple[CareerTimeline, ...]
    ) -> CareerTimeline:
        """Combine supplied inventories while preserving duplicates and conflicts."""

        require_privacy_gate(self._privacy_gate).assert_safe(timelines)
        events = tuple(event for timeline in timelines for event in timeline.events)
        evidence = tuple(item for timeline in timelines for item in timeline.evidence)
        source_ids = tuple(dict.fromkeys(source for timeline in timelines for source in timeline.source_ids))
        case_ids = {timeline.employee_case_id for timeline in timelines if timeline.employee_case_id is not None}
        employee_case_id = next(iter(case_ids)) if len(case_ids) == 1 else None
        return CareerTimeline(
            timeline_id=timeline_id,
            employee_case_id=employee_case_id,
            events=events,
            evidence=evidence,
            source_ids=source_ids,
            synthetic_only=all(timeline.synthetic_only for timeline in timelines),
        )
