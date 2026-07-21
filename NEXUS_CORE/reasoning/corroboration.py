"""Structural corroboration between compatible facts from distinct sources."""

from __future__ import annotations

from ._identity import stable_reasoning_id
from .models import (
    Corroboration,
    CorroborationStrength,
    Fact,
    FactCollection,
    FactCorrelation,
)


def _periods_compatible(left: Fact, right: Fact) -> bool:
    if left.period is None or right.period is None:
        return True
    return left.period.overlaps(right.period)


class CorroborationEngine:
    def identify(
        self,
        facts: FactCollection,
        correlations: tuple[FactCorrelation, ...],
    ) -> tuple[Corroboration, ...]:
        found = []
        for correlation in correlations:
            correlated = [facts.find(reference) for reference in correlation.fact_references]
            candidates = [fact for fact in correlated if fact is not None]
            groups: list[list[Fact]] = []
            for fact in candidates:
                matching = next(
                    (
                        group
                        for group in groups
                        if fact.value == group[0].value
                        and all(_periods_compatible(fact, existing) for existing in group)
                    ),
                    None,
                )
                if matching is None:
                    groups.append([fact])
                else:
                    matching.append(fact)

            for group in groups:
                source_ids = tuple(
                    sorted(
                        {fact.provenance.source.source_id for fact in group},
                        key=lambda identifier: identifier.value,
                    )
                )
                if len(group) < 2 or len(source_ids) < 2:
                    continue
                fact_ids = tuple(
                    fact.fact_id for fact in sorted(group, key=lambda item: item.fact_id.value)
                )
                period = group[0].period if all(fact.period == group[0].period for fact in group) else None
                found.append(
                    Corroboration(
                        corroboration_id=stable_reasoning_id(
                            "corroboration", tuple(item.value for item in fact_ids)
                        ),
                        fact_references=fact_ids,
                        source_references=source_ids,
                        strength=self._strength(len(source_ids)),
                        period=period,
                    )
                )
        return tuple(sorted(found, key=lambda item: item.corroboration_id.value))

    @staticmethod
    def _strength(source_count: int) -> CorroborationStrength:
        if source_count == 2:
            return CorroborationStrength.TWO_DISTINCT_SOURCES
        if source_count == 3:
            return CorroborationStrength.THREE_DISTINCT_SOURCES
        return CorroborationStrength.MULTIPLE_DISTINCT_SOURCES
