"""Public contracts for the architecture-only career timeline LOT."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .career_timeline_models import CareerEvent, CareerTimeline, TimelineReport


@dataclass(frozen=True)
class CareerTimelineContract:
    """Safety declaration governing the structural timeline service."""

    status: str = "ARCHITECTURE_ONLY"
    enabled: bool = False
    calculation_allowed: bool = False
    simulation_allowed: bool = False
    network_allowed: bool = False
    scraping_allowed: bool = False
    download_allowed: bool = False
    real_documents_allowed: bool = False


class CareerTimelinePort(Protocol):
    """Stable public operations exposed by the timeline engine."""

    def create_empty_timeline(
        self, timeline_id: str, employee_case_id: str | None = None
    ) -> CareerTimeline: ...

    def add_event(self, timeline: CareerTimeline, event: CareerEvent) -> CareerTimeline: ...

    def remove_event(self, timeline: CareerTimeline, event_id: str) -> CareerTimeline: ...

    def validate(self, timeline: CareerTimeline): ...

    def generate_report(self, timeline: CareerTimeline) -> TimelineReport: ...

    def merge_sources(
        self, timeline_id: str, timelines: tuple[CareerTimeline, ...]
    ) -> CareerTimeline: ...


CAREER_TIMELINE_CONTRACT = CareerTimelineContract()


CAREER_TIMELINE_FUTURE_SOURCES = (
    "PAYROLL_ENGINE",
    "LEGAL_ENGINE",
    "CSE_ENGINE",
    "CSSCT_ENGINE",
    "RETIREMENT_ENGINE",
    "SOCIAL_PROTECTION_ENGINE",
    "AGGREGATED_SOCIAL_REPORT",
    "INEOS_AGREEMENTS",
    "IMPORTED_DOCUMENT_REFERENCES",
)
"""Declared future enrichers; LOT 2 does not connect to or execute them."""
