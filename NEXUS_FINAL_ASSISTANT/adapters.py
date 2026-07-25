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
        missing_information=missing,
        questions=missing,
        sources=_source_items(payload),
        strategies=strategies,
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
                text = item.get("message") or item.get("title") or item.get("label") or item.get("description")
                if text:
                    output.append(str(text))
            elif str(item).strip():
                output.append(str(item))
        return tuple(output)
    return (str(value),)


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
            output.append(SourceItem(str(item.get("type") or "official"), title))
    return tuple(output)
