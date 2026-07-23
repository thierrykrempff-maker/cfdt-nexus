"""Explicit preservation of Retirement conflicts in generic Core models."""

from __future__ import annotations

from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_models import ReconstructionProposal
from RETIREMENT_PENIBILITY_ENGINE.rule_reasoning_models import ReasoningOutcome
from NEXUS_CORE.conflict_resolution import ResolutionCandidate, ResolutionCategory
from NEXUS_CORE.identifiers import EntityId
from NEXUS_CORE.reasoning import ConflictExplanation, ReasoningConflict

from ._identity import stable_retirement_id


class RetirementConflictMapper:
    """Preserve conflicts and candidates without selecting or arbitrating them."""

    def map(self, reconstruction: ReconstructionProposal | None,
            reasoning: ReasoningOutcome | None) -> tuple[
                tuple[ReasoningConflict, ...], tuple[ResolutionCandidate, ...]
            ]:
        conflicts: list[ReasoningConflict] = []
        candidates: list[ResolutionCandidate] = []
        if reconstruction is not None:
            for item in reconstruction.conflicts:
                refs = self._fact_refs(item.conflict_id, item.record_ids)
                conflict_id = EntityId(stable_retirement_id("conflict", "reconstruction", item.conflict_id))
                conflicts.append(ReasoningConflict(
                    conflict_id,
                    refs,
                    ConflictExplanation(
                        "RETIREMENT_RECONSTRUCTION_CONFLICT",
                        item.conflict_type.value,
                        refs,
                    ),
                    None,
                ))
                candidates.append(ResolutionCandidate(
                    EntityId(stable_retirement_id("candidate", item.conflict_id)),
                    self._category(item.conflict_type.value),
                    "RETIREMENT_REVIEW_CANDIDATE",
                    fact_references=refs,
                ))
        if reasoning is not None:
            for item in reasoning.conflicts:
                refs = self._fact_refs(item.conflict_id, (item.rule_id, item.condition_id))
                conflicts.append(ReasoningConflict(
                    EntityId(stable_retirement_id("conflict", "reasoning", item.conflict_id)),
                    refs,
                    ConflictExplanation("RETIREMENT_RULE_CONFLICT", "RULE_CONFLICT", refs),
                    None,
                ))
                candidates.append(ResolutionCandidate(
                    EntityId(stable_retirement_id("candidate", "reasoning", item.conflict_id)),
                    ResolutionCategory.UNRESOLVED,
                    "RETIREMENT_RULE_REVIEW_CANDIDATE",
                    fact_references=refs,
                ))
        return tuple(conflicts), tuple(candidates)

    @staticmethod
    def _fact_refs(conflict_id: str, values: tuple[str, ...]) -> tuple[EntityId, ...]:
        normalized = values if len(values) >= 2 else values + ("missing_counterpart",)
        return tuple(EntityId(stable_retirement_id("fact", conflict_id, value)) for value in normalized)

    @staticmethod
    def _category(code: str) -> ResolutionCategory:
        if "DATE" in code:
            return ResolutionCategory.TEMPORAL_CONFLICT
        if "SOURCE" in code or "PROVENANCE" in code:
            return ResolutionCategory.SOURCE_CONFLICT
        return ResolutionCategory.DOCUMENT_CONFLICT
