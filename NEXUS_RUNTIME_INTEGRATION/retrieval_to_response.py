"""Opt-in propagation from retrieval execution to the final response pipeline."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Mapping

from SYNDICAL_REASONING_ENGINE import (
    CaseFactualCore,
    ConnectorExecutionSummary,
    EvidenceSelection,
    EvidenceSourceType,
    ResearchPlan,
    build_evidence_bundles,
    build_research_plan,
    select_evidence,
)

from .source_execution_runtime import (
    SourceExecutionRuntime,
    SourceExecutionRuntimeConfig,
)


ENV_RETRIEVAL_TO_FINAL_RESPONSE_ENABLED = (
    "NEXUS_RETRIEVAL_TO_FINAL_RESPONSE_ENABLED"
)


def _enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class RetrievalToResponseConfig:
    enabled: bool = False

    @classmethod
    def from_env(cls) -> "RetrievalToResponseConfig":
        return cls(_enabled(os.environ.get(ENV_RETRIEVAL_TO_FINAL_RESPONSE_ENABLED)))


@dataclass(frozen=True, slots=True)
class RetrievalToResponseResult:
    called: bool
    plan: ResearchPlan | None = None
    summary: ConnectorExecutionSummary | None = None
    selection: EvidenceSelection | None = None
    fallback_code: str | None = None

    @property
    def source_records(self) -> tuple[dict[str, object], ...]:
        if not self.selection:
            return ()
        return tuple(item.to_source_record() for item in self.selection.selected)

    @property
    def public_evidence(self) -> tuple[dict[str, object], ...]:
        if not self.selection:
            return ()
        return tuple(item.to_dict(public=True) for item in self.selection.selected)

    @property
    def public_minutes(self) -> tuple[dict[str, object], ...]:
        if not self.selection:
            return ()
        return tuple(
            item.to_dict(public=True)
            for item in self.selection.selected
            if item.source_type is EvidenceSourceType.CSE_CSSCT_MINUTES
        )

    def to_dict(self, *, public: bool = False) -> dict[str, object]:
        selection = self.selection
        return {
            "enabled": self.called or bool(self.plan),
            "called": self.called,
            "fallback_code": self.fallback_code,
            "received_count": len(selection.received) if selection else 0,
            "linked_count": len(selection.received) if selection else 0,
            "selected_count": len(selection.selected) if selection else 0,
            "rejected_count": len(selection.rejected) if selection else 0,
            "evidence": list(self.public_evidence)
            if public
            else (
                [item.to_dict() for item in selection.selected]
                if selection
                else []
            ),
            "rejected": []
            if public or not selection
            else [
                {"evidence_id": evidence_id, "reason": reason}
                for evidence_id, reason in selection.rejected
            ],
        }


class RetrievalToResponseIntegration:
    """Execute the coordinator once and expose only deterministically selected evidence."""

    def __init__(
        self,
        config: RetrievalToResponseConfig | None = None,
        *,
        runtime: SourceExecutionRuntime | None = None,
    ) -> None:
        self._config = config or RetrievalToResponseConfig.from_env()
        self._runtime = runtime

    def integrate(self, core: CaseFactualCore) -> RetrievalToResponseResult:
        if not self._config.enabled:
            return RetrievalToResponseResult(False)
        plan = build_research_plan(core)
        runtime_config = SourceExecutionRuntimeConfig.from_env()
        if not runtime_config.enabled:
            return RetrievalToResponseResult(
                False,
                plan=plan,
                fallback_code="SOURCE_EXECUTION_COORDINATOR_DISABLED",
            )
        runtime = self._runtime or SourceExecutionRuntime(runtime_config)
        execution = runtime.execute(plan)
        if not execution.called or execution.summary is None:
            return RetrievalToResponseResult(
                execution.called,
                plan=plan,
                fallback_code=(
                    execution.fallback_code or "SOURCE_EXECUTION_NO_SUMMARY"
                ),
            )
        try:
            bundles = build_evidence_bundles(plan, execution.summary)
            selection = select_evidence(bundles)
        except (TypeError, ValueError):
            return RetrievalToResponseResult(
                True,
                plan=plan,
                summary=execution.summary,
                fallback_code="RETRIEVAL_EVIDENCE_MAPPING_FAILED",
            )
        return RetrievalToResponseResult(
            True,
            plan=plan,
            summary=execution.summary,
            selection=selection,
        )


def merge_retrieved_sources(
    historical_sources: object,
    result: RetrievalToResponseResult,
) -> tuple[Mapping[str, object], ...]:
    """Merge selected records without mutating or duplicating historical sources."""

    existing = tuple(
        item
        for item in (
            historical_sources
            if isinstance(historical_sources, (list, tuple))
            else ()
        )
        if isinstance(item, Mapping)
    )
    seen = {
        (
            str(item.get("provider") or item.get("origin") or "").casefold(),
            str(item.get("document") or item.get("title") or "").casefold(),
            str(
                item.get("article_or_section")
                or item.get("article")
                or item.get("location")
                or ""
            ).casefold(),
        )
        for item in existing
    }
    merged = list(existing)
    for source in result.source_records:
        key = (
            str(source.get("provider") or "").casefold(),
            str(source.get("document") or "").casefold(),
            str(source.get("article_or_section") or "").casefold(),
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(source)
    return tuple(merged)


def retain_applicable_evidence(
    result: RetrievalToResponseResult,
    applicable_sources: object,
) -> tuple[dict[str, object], ...]:
    """Keep only evidence accepted by the existing source-to-facts analysis."""

    accepted_keys = {
        (
            str(item.get("source_title") or "").strip().casefold(),
            str(item.get("article_or_clause") or "").strip().casefold(),
            str(item.get("precise_excerpt") or "").strip().casefold(),
        )
        for item in (
            applicable_sources
            if isinstance(applicable_sources, (list, tuple))
            else ()
        )
        if isinstance(item, Mapping)
        and item.get("citation_ready") is True
        and not item.get("rejection_reason")
    }
    return tuple(
        item.to_dict(public=True)
        for item in (result.selection.selected if result.selection else ())
        if (
            item.title.strip().casefold(),
            str(item.reference or "").strip().casefold(),
            str(item.excerpt or "").strip().casefold(),
        )
        in accepted_keys
    )


__all__ = (
    "ENV_RETRIEVAL_TO_FINAL_RESPONSE_ENABLED",
    "RetrievalToResponseConfig",
    "RetrievalToResponseIntegration",
    "RetrievalToResponseResult",
    "merge_retrieved_sources",
    "retain_applicable_evidence",
)
