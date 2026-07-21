"""Structural report assembly for a career timeline."""

from __future__ import annotations

from .career_timeline_models import CareerTimeline, TimelineConfidence, TimelineReport
from .career_timeline_validator import CareerTimelineValidator


class CareerTimelineReportBuilder:
    """Build reports from validation findings without business inference."""

    def __init__(self, validator: CareerTimelineValidator | None = None) -> None:
        self._validator = validator or CareerTimelineValidator()

    def build(self, timeline: CareerTimeline) -> TimelineReport:
        """Return the supplied facts and their explicit uncertainty."""

        validation = self._validator.validate(timeline)
        uncertainty = tuple(issue.description for issue in validation.issues)
        missing = tuple(
            issue.description
            for issue in validation.issues
            if issue.issue_type == "INSUFFICIENT_EVIDENCE"
        )
        return TimelineReport(
            timeline=timeline,
            events=timeline.events,
            uncertainty_zones=uncertainty,
            evidence_used=timeline.evidence,
            missing_evidence=missing,
            conflicts=validation.conflicts,
            global_confidence=TimelineConfidence.UNKNOWN,
        )
