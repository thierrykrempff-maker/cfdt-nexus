"""Aggregate explicit decision and vote findings."""

from __future__ import annotations

from NEXUS_CORE import Finding

from .decisions import CSEDecisionMapper
from .models import CSEDecisionSnapshot, CSEVoteSnapshot
from .votes import CSEVoteMapper


class CSEFindingMapper:
    def __init__(self) -> None:
        self._decisions = CSEDecisionMapper()
        self._votes = CSEVoteMapper()

    def map(self, decisions: tuple[CSEDecisionSnapshot, ...],
            votes: tuple[CSEVoteSnapshot, ...], subject, produced_at) -> tuple[Finding, ...]:
        decision_findings = tuple(
            finding
            for decision in decisions
            for finding in self._decisions.map(decision)[0]
        )
        vote_findings = tuple(
            self._votes.map(vote, subject, produced_at)[1] for vote in votes
        )
        return decision_findings + vote_findings
