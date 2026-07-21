"""Links facts sharing a subject and fact type without merging them."""

from __future__ import annotations

from collections import defaultdict

from ._identity import stable_reasoning_id
from .models import FactCollection, FactCorrelation


class FactCorrelationEngine:
    def correlate(self, facts: FactCollection) -> tuple[FactCorrelation, ...]:
        groups = defaultdict(list)
        for fact in facts.facts:
            groups[(fact.subject_reference, fact.fact_type)].append(fact)

        correlations = []
        for (subject, fact_type), grouped in groups.items():
            if len(grouped) < 2:
                continue
            references = tuple(
                fact.fact_id for fact in sorted(grouped, key=lambda item: item.fact_id.value)
            )
            correlations.append(
                FactCorrelation(
                    correlation_id=stable_reasoning_id(
                        "correlation", tuple(item.value for item in references)
                    ),
                    subject_reference=subject,
                    fact_type=fact_type,
                    fact_references=references,
                )
            )
        return tuple(sorted(correlations, key=lambda item: item.correlation_id.value))
