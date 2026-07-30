"""Opt-in propagation from retrieval execution to the final response pipeline."""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
from typing import Mapping
import unicodedata

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
from .public_evidence_safety import (
    PublicEvidenceDecision,
    sanitize_public_evidence_text,
)


ENV_RETRIEVAL_TO_FINAL_RESPONSE_ENABLED = (
    "NEXUS_RETRIEVAL_TO_FINAL_RESPONSE_ENABLED"
)
_FINAL_RELATION_STOP_WORDS = {
    "avec", "dans", "pour", "sans", "sous", "entre", "apres", "avant",
    "ainsi", "alors", "comme", "cette", "celui", "celle", "elles", "leurs",
    "des", "les", "une", "sur", "est", "sont", "ete", "etre", "doit", "dont",
    "plus", "moins", "tout", "tous", "fait", "faits", "dossier", "salarie",
    "employeur", "direction", "question", "preciser", "verifier", "mesure",
    "rechercher", "uniquement", "precedent", "contexte", "interne", "role",
    "utilise", "utiliser", "travail", "document", "source", "concernant",
}


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


@dataclass(frozen=True, slots=True)
class FinalEvidenceSelection:
    evidence: tuple[dict[str, object], ...]
    rejected: tuple[dict[str, str], ...]
    accepted_keys: tuple[tuple[str, str, str], ...]
    rejected_keys: tuple[tuple[str, str, str], ...]


def _normalize(value: object) -> str:
    decomposed = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join(
        "".join(char for char in decomposed if not unicodedata.combining(char))
        .casefold()
        .replace("'", " ")
        .replace("’", " ")
        .replace("_", " ")
        .replace("-", " ")
        .split()
    )


def _distinctive_tokens(value: object) -> set[str]:
    tokens: set[str] = set()
    for token in re.findall(r"[a-z0-9]{3,}", _normalize(value)):
        if token in _FINAL_RELATION_STOP_WORDS:
            continue
        if token in {"cse", "cssct", "chsct", "ce"}:
            tokens.add("representative_body")
            continue
        if token.startswith("badge"):
            tokens.add("badge")
            continue
        if token.startswith("equip") or token == "epi":
            tokens.add("epi")
            continue
        if token.startswith("risqu"):
            tokens.add("risque")
            continue
        for suffix in ("ements", "ement", "ations", "ation", "ees", "ee", "es", "er", "e", "s"):
            if token.endswith(suffix) and len(token) - len(suffix) >= 5:
                token = token[: -len(suffix)]
                break
        tokens.add(token)
    return tokens


def _evidence_key(value: Mapping[str, object]) -> tuple[str, str, str]:
    return (
        str(value.get("source_title") or value.get("title") or "").strip().casefold(),
        str(value.get("article_or_clause") or value.get("reference") or "").strip().casefold(),
        str(value.get("precise_excerpt") or value.get("excerpt") or "").strip().casefold(),
    )


def evaluate_applicable_evidence(
    result: RetrievalToResponseResult,
    applicable_sources: object,
) -> FinalEvidenceSelection:
    """Recheck factual, legal and research-purpose relations before publication."""

    accepted_by_source_to_facts = {
        _evidence_key(item)
        for item in (
            applicable_sources
            if isinstance(applicable_sources, (list, tuple))
            else ()
        )
        if isinstance(item, Mapping)
        and item.get("citation_ready") is True
        and not item.get("rejection_reason")
    }
    plan = result.plan
    issues = {item.issue_id: item for item in plan.issues} if plan else {}
    queries = {
        item.query_id: item
        for item in ((*plan.queries, *plan.blocked_queries) if plan else ())
    }
    evidence: list[dict[str, object]] = []
    rejected: list[dict[str, str]] = []
    accepted_keys: list[tuple[str, str, str]] = []
    rejected_keys: list[tuple[str, str, str]] = []
    seen_contributions: set[tuple[str, str, str]] = set()

    for bundle in result.selection.selected if result.selection else ():
        key = (
            bundle.title.strip().casefold(),
            str(bundle.reference or "").strip().casefold(),
            str(bundle.excerpt or "").strip().casefold(),
        )
        if key not in accepted_by_source_to_facts:
            continue
        issue = issues.get(bundle.issue_id)
        query = queries.get(bundle.query_id)
        source_tokens = _distinctive_tokens(" ".join((bundle.title, bundle.excerpt or "")))
        issue_tokens = _distinctive_tokens(issue.legal_question if issue else "")
        fact_tokens = _distinctive_tokens(
            " ".join(query.factual_scope if query else ())
        )
        objective_tokens = _distinctive_tokens(bundle.research_objective)
        safe_excerpt = sanitize_public_evidence_text(bundle.excerpt)
        issue_relation = source_tokens & issue_tokens
        fact_relation = source_tokens & fact_tokens
        reason: str | None = None
        if safe_excerpt.decision is PublicEvidenceDecision.REJECTED:
            reason = "SENSITIVE_CONTENT_NOT_NECESSARY"
        elif not bundle.fact_ids or not (fact_relation or issue_relation):
            reason = "INSUFFICIENT_FINAL_FACTUAL_RELATION"
        elif not issue_relation:
            reason = "INSUFFICIENT_LEGAL_ISSUE_RELATION"
        elif not (source_tokens & objective_tokens):
            reason = "DISTINCTIVE_CONCEPT_MISSING"
        contribution_key = (
            bundle.issue_id,
            " ".join(sorted(issue_relation)),
            " ".join(sorted(fact_relation)),
        )
        if reason is None and contribution_key in seen_contributions:
            reason = "REDUNDANT_EVIDENCE"
        if reason:
            rejected.append(
                {
                    "source_reference": bundle.title,
                    "reason": reason,
                }
            )
            rejected_keys.append(key)
            continue
        seen_contributions.add(contribution_key)
        public = bundle.to_dict(public=True)
        public["excerpt"] = safe_excerpt.text
        evidence.append(public)
        accepted_keys.append(key)
    return FinalEvidenceSelection(
        tuple(evidence),
        tuple(rejected),
        tuple(accepted_keys),
        tuple(rejected_keys),
    )


def apply_final_evidence_selection(
    source_to_facts_payload: Mapping[str, object],
    selection: FinalEvidenceSelection,
) -> dict[str, object]:
    """Remove finally rejected retrieval evidence from all downstream projections."""

    rejected_keys = set(selection.rejected_keys)
    rejected_title_excerpt = {(title, excerpt) for title, _reference, excerpt in rejected_keys}
    applicable = [
        item
        for item in source_to_facts_payload.get("applicable_sources", ())
        if not (
            isinstance(item, Mapping)
            and (
                _evidence_key(item) in rejected_keys
                or (
                    str(item.get("source_title") or "").strip().casefold(),
                    str(item.get("precise_excerpt") or "").strip().casefold(),
                )
                in rejected_title_excerpt
            )
        )
    ]
    comparisons = [
        item
        for item in source_to_facts_payload.get("rule_to_facts_analysis", ())
        if not (
            isinstance(item, Mapping)
            and any(
                title
                and title
                in str(item.get("source_reference") or "").strip().casefold()
                and excerpt
                == str(item.get("rule_summary") or "").strip().casefold()
                for title, _reference, excerpt in rejected_keys
            )
        )
    ]
    existing_rejections = [
        dict(item)
        for item in source_to_facts_payload.get("rejected_sources", ())
        if isinstance(item, Mapping)
    ]
    output = dict(source_to_facts_payload)
    output["applicable_sources"] = applicable
    output["rule_to_facts_analysis"] = comparisons
    output["rejected_sources"] = [*existing_rejections, *selection.rejected]
    return output


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
        _evidence_key(item)
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
    "FinalEvidenceSelection",
    "apply_final_evidence_selection",
    "evaluate_applicable_evidence",
    "merge_retrieved_sources",
    "retain_applicable_evidence",
)
