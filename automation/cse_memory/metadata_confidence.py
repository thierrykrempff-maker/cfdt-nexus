"""Deterministic confidence calculation and arbitration."""
from __future__ import annotations
from collections import defaultdict
from typing import Any
from automation.cse_memory.metadata_models import MetadataValue

SOURCE_WEIGHTS = {"first_block": .90, "internal_title": .85, "filename": .72, "folder": .35, "technical": .15, "body": .45}

def confidence_level(value: float) -> str:
    if value >= .90: return "very_high"
    if value >= .75: return "high"
    if value >= .50: return "medium"
    if value >= .25: return "low"
    return "very_low"

def arbitrate(candidates: list[dict[str, Any]], missing_rule: str) -> MetadataValue:
    if not candidates:
        return MetadataValue(rule_id=missing_rule, warnings=["metadata_missing"])
    grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates: grouped[candidate["value"]].append(candidate)
    ranked = []
    for value, items in grouped.items():
        sources = sorted({item["source"] for item in items})
        base = max(item["weight"] for item in items)
        score = min(.99, base + .08 * (len(sources) - 1))
        ranked.append((score, value, items, sources))
    ranked.sort(key=lambda row: -row[0])
    score, value, items, sources = ranked[0]
    alternatives = [{"value": row[1], "confidence": round(row[0], 3)} for row in ranked[1:]]
    warnings = ["conflicting_candidates"] if alternatives else []
    rule = items[0]["rule_id"] if len(sources) == 1 else items[0].get("agreement_rule", "MULTIPLE_SOURCES_AGREE")
    return MetadataValue(value=value, confidence=round(score, 3), confidence_level=confidence_level(score), detected_from=sources, evidence_type=items[0].get("evidence_type", "pattern"), rule_id=rule, alternatives=alternatives, warnings=warnings)

def metadata_quality(values: dict[str, MetadataValue], conflicts: list[dict[str, Any]]) -> tuple[int, str]:
    important = ("meeting_date", "instance", "document_kind", "title", "document_status")
    score = round(sum(values[key].confidence for key in important) / len(important) * 100) if values else 0
    score = max(0, score - min(30, len(conflicts) * 10))
    level = "excellent" if score >= 90 else "good" if score >= 75 else "acceptable" if score >= 55 else "poor" if score >= 25 else "unusable"
    return score, level
