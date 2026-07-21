"""Technical documentary coherence assessment with no legal meaning."""

from __future__ import annotations

from ..conflicts import ConflictReason, EvidenceConflict
from ..evidence import Evidence
from ..evidence_graph import EvidenceGraph, EvidenceRelationType
from ..reasoning.models import Fact, ReasoningReport
from .models import CoherenceAssessment


class CoherenceEvaluator:
    """Evaluate five neutral structural dimensions on a zero-to-one scale."""

    def evaluate(
        self,
        report: ReasoningReport,
        graph: EvidenceGraph | None = None,
        evidence: tuple[Evidence, ...] = (),
        conflicts: tuple[EvidenceConflict, ...] = (),
        facts: tuple[Fact, ...] = (),
    ) -> CoherenceAssessment:
        all_facts = self._facts(report, facts)
        fact_count = len(all_facts)
        contradiction_edges = 0 if graph is None else sum(
            edge.relation_type is EvidenceRelationType.CONTRADICTS for edge in graph.edges
        )
        conflict_count = len(report.conflicts) + len(conflicts) + contradiction_edges
        temporal_conflicts = sum(
            "PERIOD" in item.explanation.code.upper()
            or "TEMPORAL" in item.explanation.code.upper()
            for item in report.conflicts
        ) + sum(item.reason is ConflictReason.PERIOD_MISMATCH for item in conflicts)
        temporal = self._ratio_penalty(temporal_conflicts, max(fact_count, 1))
        documentary = self._ratio_penalty(conflict_count, max(fact_count, 1))

        corroborated = {
            reference
            for item in report.corroborations
            for reference in item.fact_references
        }
        corroboration = len(corroborated) / fact_count if fact_count else 0.0

        sources = {fact.provenance.source.source_id for fact in all_facts}
        sources.update(item.provenance.source.source_id for item in evidence)
        evidence_base = max(fact_count, len(evidence))
        provenance = min(1.0, len(sources) / evidence_base) if evidence_base else 0.0

        missing_count = len(report.missing_evidence)
        completeness = fact_count / (fact_count + missing_count) if fact_count + missing_count else 0.0
        dimensions = (temporal, documentary, corroboration, provenance, completeness)
        overall = round(sum(dimensions) / len(dimensions), 6)
        return CoherenceAssessment(
            round(temporal, 6),
            round(documentary, 6),
            round(corroboration, 6),
            round(provenance, 6),
            round(completeness, 6),
            overall,
            (
                "TEMPORAL_STRUCTURE",
                "DOCUMENTARY_STRUCTURE",
                "DISTINCT_SOURCE_CORROBORATION",
                "PROVENANCE_COVERAGE",
                "EVIDENCE_COMPLETENESS",
            ),
        )

    @staticmethod
    def _ratio_penalty(count: int, denominator: int) -> float:
        return max(0.0, 1.0 - count / denominator)

    @staticmethod
    def _facts(report: ReasoningReport, facts: tuple[Fact, ...]) -> tuple[Fact, ...]:
        by_id = {fact.fact_id: fact for fact in report.facts.facts}
        by_id.update({fact.fact_id: fact for fact in facts})
        return tuple(by_id.values())
