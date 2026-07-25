"""Source hierarchy and deterministic fusion."""

from __future__ import annotations

from .models import SourceItem

_PRIORITY = {
    "agreements_ineos": 100,
    "accord_entreprise": 100,
    "collective_agreement": 90,
    "convention_collective": 90,
    "labor_code": 80,
    "code_travail": 80,
    "social_security_code": 80,
    "case_law": 70,
    "jurisprudence": 70,
    "cse_document": 60,
    "cse_history": 60,
    "official": 50,
    "individual_document": 40,
    "factual_system": 30,
    "testimony": 10,
}


def merge_sources(items: tuple[SourceItem, ...]) -> tuple[SourceItem, ...]:
    selected: dict[tuple[str, str, str | None], SourceItem] = {}
    for item in items:
        key = (item.source_type, item.title.casefold(), item.date)
        reliability = item.reliability or _PRIORITY.get(item.source_type, 0)
        normalized = SourceItem(
            item.source_type,
            item.title,
            item.date,
            item.relevance,
            item.reasoning_role,
            reliability,
            item.document_to_verify,
            item.confidential,
        )
        previous = selected.get(key)
        if previous is None or normalized.reliability > previous.reliability:
            selected[key] = normalized
    return tuple(
        sorted(
            selected.values(),
            key=lambda item: (-item.reliability, item.title.casefold(), item.date or ""),
        )
    )
