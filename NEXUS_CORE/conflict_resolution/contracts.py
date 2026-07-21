"""Public structural contracts for documentary conflict resolution."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from ..conflicts import EvidenceConflict
from ..evidence import Evidence
from ..evidence_graph import EvidenceGraph
from ..findings import Finding
from ..identifiers import EntityId
from ..reasoning.models import Fact, ReasoningReport
from .models import ResolutionReport


@runtime_checkable
class ConflictResolutionEngine(Protocol):
    def resolve(
        self,
        report_id: EntityId,
        reasoning_report: ReasoningReport,
        created_at: datetime,
        evidence_graph: EvidenceGraph | None = None,
        evidence: tuple[Evidence, ...] = (),
        findings: tuple[Finding, ...] = (),
        conflicts: tuple[EvidenceConflict, ...] = (),
        facts: tuple[Fact, ...] = (),
    ) -> ResolutionReport: ...


@runtime_checkable
class ResolutionReporter(Protocol):
    def render(self, report: ResolutionReport) -> str: ...
