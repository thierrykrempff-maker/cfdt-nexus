"""Extension contracts for Evidence Graph builders and exporters."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..analysis import DomainAnalysisResult
from ..identifiers import EntityId
from .graph import EvidenceGraph


@runtime_checkable
class EvidenceGraphBuilder(Protocol):
    def build(
        self, graph_id: EntityId, results: tuple[DomainAnalysisResult, ...]
    ) -> EvidenceGraph: ...


@runtime_checkable
class EvidenceGraphExporter(Protocol):
    def export(self, graph: EvidenceGraph) -> str: ...
