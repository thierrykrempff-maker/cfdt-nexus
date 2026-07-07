"""Small shared helpers for local Nexus experts."""

from __future__ import annotations

import unicodedata
from typing import Any, Iterable


def normalize(value: Any) -> str:
    text = str(value or "").casefold()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.replace("'", " ").replace("’", " ")


def has_any(value: Any, keywords: Iterable[str]) -> bool:
    text = normalize(value)
    return any(normalize(keyword) in text for keyword in keywords)


def route_domains(answer: dict[str, Any]) -> set[str]:
    route = answer.get("route", {})
    return {str(domain) for domain in route.get("domains", [])}


def unique(values: Iterable[Any], limit: int | None = None) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue
        key = normalize(value)
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
        if limit is not None and len(result) >= limit:
            break
    return result


def source_label(source: dict[str, Any]) -> str:
    parts = [str(source.get("document") or "Document local")]
    if source.get("page"):
        parts.append(f"page {source['page']}")
    if source.get("article"):
        parts.append(str(source["article"]))
    return " | ".join(parts)


def source_documents(answer: dict[str, Any], limit: int | None = None) -> list[str]:
    return unique((source_label(source) for source in answer.get("sources", [])), limit=limit)


def issue_group(answer: dict[str, Any], group_id: str) -> dict[str, Any] | None:
    for group in answer.get("issue_groups", []):
        if group.get("id") == group_id:
            return group
    return None


def collect_issue_values(answer: dict[str, Any], field: str) -> list[str]:
    values: list[str] = []
    for group in answer.get("issue_groups", []):
        values.extend(str(item) for item in group.get(field, []) if item)
    return unique(values)
