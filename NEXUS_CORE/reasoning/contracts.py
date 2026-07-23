"""Structural contracts for future domain reasoning adapters."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from ..entities import EntityReference
from ..evidence import Evidence
from ..identifiers import EntityId
from ..periods import Period
from .models import FactCollection, FactType, ReasoningReport


@runtime_checkable
class FactProducer(Protocol):
    def extract(self, evidence: tuple[Evidence, ...]) -> FactCollection: ...


@runtime_checkable
class ReasoningEngine(Protocol):
    def reason(
        self,
        report_id: EntityId,
        evidence: tuple[Evidence, ...],
        subject: EntityReference,
        required_fact_types: tuple[FactType, ...],
        created_at: datetime,
        required_period: Period | None = None,
    ) -> ReasoningReport: ...


@runtime_checkable
class ReasoningReporter(Protocol):
    def render(self, report: ReasoningReport) -> str: ...
