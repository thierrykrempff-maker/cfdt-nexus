"""Aggregate recommendations explicitly declared by CSE decisions."""

from __future__ import annotations

from NEXUS_CORE import Recommendation

from .decisions import CSEDecisionMapper
from .models import CSEDecisionSnapshot


class CSERecommendationMapper:
    def __init__(self) -> None:
        self._decisions = CSEDecisionMapper()

    def map(self, decisions: tuple[CSEDecisionSnapshot, ...]) -> tuple[Recommendation, ...]:
        return tuple(
            recommendation
            for decision in decisions
            for recommendation in self._decisions.map(decision)[1]
        )
