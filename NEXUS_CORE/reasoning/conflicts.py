"""Conflict detection and neutral explanation without arbitration."""

from __future__ import annotations

from itertools import combinations

from ._identity import stable_reasoning_id
from .corroboration import _periods_compatible
from .models import (
    ConflictExplanation,
    FactCollection,
    FactCorrelation,
    ReasoningConflict,
)


class ConflictEngine:
    def detect(
        self,
        facts: FactCollection,
        correlations: tuple[FactCorrelation, ...],
    ) -> tuple[ReasoningConflict, ...]:
        conflicts = []
        for correlation in correlations:
            correlated = [facts.find(reference) for reference in correlation.fact_references]
            present = [fact for fact in correlated if fact is not None]
            for left, right in combinations(present, 2):
                if not _periods_compatible(left, right) or left.value == right.value:
                    continue
                references = tuple(sorted((left.fact_id, right.fact_id), key=lambda item: item.value))
                conflict_id = stable_reasoning_id(
                    "reasoning-conflict", tuple(item.value for item in references)
                )
                period = left.period if left.period == right.period else None
                explanation = ConflictExplanation(
                    code="FACT_VALUE_MISMATCH",
                    category="structural_conflict",
                    fact_references=references,
                )
                conflicts.append(
                    ReasoningConflict(
                        conflict_id=conflict_id,
                        fact_references=references,
                        explanation=explanation,
                        period=period,
                    )
                )
        unique = {conflict.conflict_id: conflict for conflict in conflicts}
        return tuple(unique[key] for key in sorted(unique, key=lambda item: item.value))
