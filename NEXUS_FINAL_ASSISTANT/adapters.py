"""Explicit adapters from heterogeneous engine payloads to the common result."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .models import Confidence, Domain, NormalizedEngineResult, SourceItem


def adapt_engine_payload(engine: str, domain: Domain, payload: Mapping[str, Any]) -> NormalizedEngineResult:
    mode = str(payload.get("mode") or "SUCCEEDED").upper()
    available = mode in {"SUCCEEDED", "CORE_V3", "ACTIVE"}
    diagnostics = payload.get("diagnostics") if isinstance(payload.get("diagnostics"), Mapping) else {}
    analysis = payload.get("analysis") if isinstance(payload.get("analysis"), Mapping) else {}
    short = payload.get("short_view") if isinstance(payload.get("short_view"), Mapping) else {}
    domain_analysis = payload.get("domain_analysis") if isinstance(payload.get("domain_analysis"), Mapping) else {}
    errors = ()
    fallback = diagnostics.get("fallback_code")
    if fallback:
        errors = (str(fallback),)
    qualifications = _strings(
        analysis.get("findings")
        or domain_analysis.get("qualifications")
        or domain_analysis.get("qualification_candidates")
        or short.get("hypotheses")
    )
    missing = _strings(
        analysis.get("missing_information")
        or domain_analysis.get("missing_information")
        or short.get("incertitudes")
    )
    strategies = _strings(
        analysis.get("recommendations")
        or domain_analysis.get("strategies")
        or short.get("strategie")
    )
    return NormalizedEngineResult(
        engine=engine,
        domain=domain,
        available=available,
        possible_qualifications=qualifications,
        retained_facts=_strings(
            analysis.get("retained_facts")
            or domain_analysis.get("retained_facts")
            or short.get("situation")
        ),
        missing_information=missing,
        questions=missing,
        sources=_source_items(payload),
        strategies=strategies,
        employee_arguments=_position_strings(
            analysis.get("employee_arguments")
            or domain_analysis.get("employee_position")
        ),
        employer_arguments=_position_strings(
            analysis.get("employer_arguments")
            or domain_analysis.get("employer_position")
        ),
        possible_actions=_strings(
            analysis.get("possible_actions")
            or domain_analysis.get("document_requests")
        ),
        confidence=Confidence.MEDIUM if available else Confidence.LOW,
        limits=("Résultat partiel à vérifier.",) if not available else (),
        technical_errors=errors,
        metadata=(("mode", mode),),
    )


def documentary_result(domain: Domain, sources: tuple[SourceItem, ...]) -> NormalizedEngineResult:
    return NormalizedEngineResult(
        "documentary",
        domain,
        available=bool(sources),
        sources=sources,
        confidence=Confidence.MEDIUM if sources else Confidence.LOW,
        limits=() if sources else ("Aucune source documentaire exploitable.",),
    )


def _strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, Mapping):
        return tuple(str(item) for item in value.values() if str(item).strip())
    if isinstance(value, (list, tuple)):
        output = []
        for item in value:
            if isinstance(item, Mapping):
                text = (
                    item.get("message")
                    or item.get("title")
                    or item.get("label")
                    or item.get("description")
                    or item.get("rationale")
                    or item.get("question")
                )
                if text:
                    output.append(str(text))
            elif str(item).strip():
                output.append(str(item))
        return tuple(output)
    return (str(value),)


def _position_strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, Mapping):
        return _strings(value)
    output = []
    for items in value.values():
        if isinstance(items, (list, tuple)):
            output.extend(str(item) for item in items if str(item).strip())
        elif isinstance(items, str) and items.strip():
            output.append(items)
    return tuple(dict.fromkeys(output))


def _source_items(payload: Mapping[str, Any]) -> tuple[SourceItem, ...]:
    raw = payload.get("sources")
    if not isinstance(raw, (list, tuple)):
        return ()
    output = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        title = str(item.get("title") or item.get("label") or item.get("source") or "").strip()
        if title:
            source_type = str(
                item.get("source_layer")
                or item.get("type")
                or item.get("origin")
                or "official"
            )
            output.append(
                SourceItem(
                    source_type,
                    title,
                    str(item.get("decision_date") or item.get("date") or "") or None,
                    reasoning_role=str(item.get("reasoning_role") or "to_verify"),
                    document_to_verify=str(
                        item.get("article")
                        or item.get("article_or_section")
                        or item.get("case_number")
                        or ""
                    )
                    or None,
                )
            )
    return tuple(output)
