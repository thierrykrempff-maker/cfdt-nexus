"""Structural classification without arbitration or documentary priority."""

from __future__ import annotations

from ..conflicts import ConflictReason, EvidenceConflict
from ..evidence_graph import EvidenceGraph, EvidenceRelationType
from ..findings import Finding, FindingType
from ..reasoning.models import (
    CorroborationStrength,
    Fact,
    ReasoningReport,
)
from ._identity import stable_resolution_id
from .models import ResolutionCandidate, ResolutionCategory, ResolutionClassification


_EXPLANATIONS = {
    ResolutionCategory.NO_CONFLICT: "NO_STRUCTURAL_CONFLICT_DETECTED",
    ResolutionCategory.DOCUMENT_CONFLICT: "DIFFERENT_VALUES_FOR_COMPATIBLE_FACTS",
    ResolutionCategory.TEMPORAL_CONFLICT: "INCOMPATIBLE_PERIODS_DETECTED",
    ResolutionCategory.SOURCE_CONFLICT: "INCONSISTENT_SOURCE_RELATIONS_DETECTED",
    ResolutionCategory.MISSING_EVIDENCE: "EXPECTED_EVIDENCE_NOT_AVAILABLE",
    ResolutionCategory.INSUFFICIENT_EVIDENCE: "EVIDENCE_SET_TOO_SMALL",
    ResolutionCategory.PARTIAL_CORROBORATION: "LIMITED_DISTINCT_SOURCE_SUPPORT",
    ResolutionCategory.STRONG_CORROBORATION: "MULTIPLE_DISTINCT_SOURCES_SUPPORT",
    ResolutionCategory.MULTIPLE_HYPOTHESES: "MORE_THAN_TWO_ALTERNATIVES_PRESERVED",
    ResolutionCategory.UNRESOLVED: "CONFLICT_PRESERVED_WITHOUT_ARBITRATION",
}


class ResolutionClassifier:
    """Classify observed structures while preserving every alternative."""

    def classify(
        self,
        report: ReasoningReport,
        graph: EvidenceGraph | None = None,
        findings: tuple[Finding, ...] = (),
        conflicts: tuple[EvidenceConflict, ...] = (),
        facts: tuple[Fact, ...] = (),
    ) -> tuple[tuple[ResolutionCandidate, ...], tuple[ResolutionClassification, ...]]:
        categories: set[ResolutionCategory] = set()
        all_facts = self._merge_facts(report, facts)
        categories.update(self._reasoning_conflicts(report))
        categories.update(self._evidence_conflicts(conflicts))

        if graph is not None and any(
            edge.relation_type is EvidenceRelationType.CONTRADICTS
            for edge in graph.edges
        ):
            categories.add(ResolutionCategory.DOCUMENT_CONFLICT)
        if any(item.finding_type is FindingType.CONFLICT for item in findings):
            categories.add(ResolutionCategory.DOCUMENT_CONFLICT)
        if report.missing_evidence or any(
            item.finding_type in {FindingType.MISSING_DOCUMENT, FindingType.MISSING_INFORMATION}
            for item in findings
        ):
            categories.add(ResolutionCategory.MISSING_EVIDENCE)
        if len(all_facts) < 2:
            categories.add(ResolutionCategory.INSUFFICIENT_EVIDENCE)

        for corroboration in report.corroborations:
            if corroboration.strength is CorroborationStrength.TWO_DISTINCT_SOURCES:
                categories.add(ResolutionCategory.PARTIAL_CORROBORATION)
            else:
                categories.add(ResolutionCategory.STRONG_CORROBORATION)

        conflict_sizes = [len(item.fact_references) for item in report.conflicts]
        conflict_sizes.extend(len(item.evidence_references) for item in conflicts)
        if any(size > 2 for size in conflict_sizes):
            categories.add(ResolutionCategory.MULTIPLE_HYPOTHESES)
        if conflict_sizes:
            categories.add(ResolutionCategory.UNRESOLVED)
        conflict_categories = {
            ResolutionCategory.DOCUMENT_CONFLICT,
            ResolutionCategory.TEMPORAL_CONFLICT,
            ResolutionCategory.SOURCE_CONFLICT,
            ResolutionCategory.MULTIPLE_HYPOTHESES,
            ResolutionCategory.UNRESOLVED,
        }
        if not categories & conflict_categories:
            categories.add(ResolutionCategory.NO_CONFLICT)

        candidates = tuple(self._candidate(category, report, conflicts) for category in categories)
        candidates = tuple(sorted(candidates, key=lambda item: item.category.value))
        classifications = tuple(
            ResolutionClassification(
                stable_resolution_id("classification", candidate.category.value),
                candidate.category,
                candidate.explanation_code,
                (candidate.candidate_id,),
            )
            for candidate in candidates
        )
        return candidates, classifications

    @staticmethod
    def explanation_for(category: ResolutionCategory) -> str:
        return _EXPLANATIONS[category]

    @staticmethod
    def _merge_facts(report: ReasoningReport, facts: tuple[Fact, ...]) -> tuple[Fact, ...]:
        by_id = {fact.fact_id: fact for fact in report.facts.facts}
        by_id.update({fact.fact_id: fact for fact in facts})
        return tuple(sorted(by_id.values(), key=lambda item: item.fact_id.value))

    @staticmethod
    def _reasoning_conflicts(report: ReasoningReport) -> set[ResolutionCategory]:
        categories = set()
        for conflict in report.conflicts:
            code = conflict.explanation.code.upper()
            if "PERIOD" in code or "TEMPORAL" in code:
                categories.add(ResolutionCategory.TEMPORAL_CONFLICT)
            elif "SOURCE" in code or "PROVENANCE" in code:
                categories.add(ResolutionCategory.SOURCE_CONFLICT)
            else:
                categories.add(ResolutionCategory.DOCUMENT_CONFLICT)
        return categories

    @staticmethod
    def _evidence_conflicts(
        conflicts: tuple[EvidenceConflict, ...],
    ) -> set[ResolutionCategory]:
        mapping = {
            ConflictReason.PERIOD_MISMATCH: ResolutionCategory.TEMPORAL_CONFLICT,
            ConflictReason.SOURCE_MISMATCH: ResolutionCategory.SOURCE_CONFLICT,
        }
        return {
            mapping.get(item.reason, ResolutionCategory.DOCUMENT_CONFLICT)
            for item in conflicts
        }

    def _candidate(
        self,
        category: ResolutionCategory,
        report: ReasoningReport,
        conflicts: tuple[EvidenceConflict, ...],
    ) -> ResolutionCandidate:
        fact_references = tuple(
            sorted(
                {reference for item in report.conflicts for reference in item.fact_references},
                key=lambda item: item.value,
            )
        )
        evidence_references = tuple(
            sorted(
                {reference for item in conflicts for reference in item.evidence_references},
                key=lambda item: item.value,
            )
        )
        return ResolutionCandidate(
            stable_resolution_id("candidate", category.value),
            category,
            self.explanation_for(category),
            evidence_references,
            fact_references,
        )
