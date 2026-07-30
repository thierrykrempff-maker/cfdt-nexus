"""Central safety gate for evidence exposed in public Runtime projections."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Mapping, Sequence


class PublicEvidenceDecision(str, Enum):
    SAFE = "SAFE"
    GENERALIZED = "GENERALIZED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class PublicEvidenceSanitization:
    text: str | None
    decision: PublicEvidenceDecision
    categories: tuple[str, ...] = ()


_SPACE = re.compile(r"\s+")
_SEGMENT = re.compile(r"(?<=[.!?;])\s+|\n+")
_HEALTH_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "PATHOLOGY_OR_DIAGNOSIS",
        re.compile(
            r"\b(?:patholog\w*|diagnosti\w*|maladie\w*|syndrome\w*|"
            r"cancer\w*|diab[eè]t\w*|infection\w*)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "TREATMENT_OR_MEDICATION",
        re.compile(
            r"\b(?:traitement\w*|m[ée]dicament\w*|prescription\w*|"
            r"hospitalis\w*|th[ée]rapie\w*)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "INDIVIDUAL_SICK_LEAVE",
        re.compile(
            r"\b(?:arr[êe]t(?:s)?\s+maladie|arr[êe]t(?:s)?\s+de\s+travail)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "FITNESS_OR_MEDICAL_RESTRICTION",
        re.compile(
            r"\b(?:inapt\w*|aptitude\s+m[ée]dicale|restriction\w*\s+m[ée]dical\w*|"
            r"am[ée]nagement\s+m[ée]dical\w*)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "DISABILITY_OR_PREGNANCY",
        re.compile(r"\b(?:handicap\w*|grossess\w*|enceinte)\b", re.IGNORECASE),
    ),
    (
        "MENTAL_HEALTH_DETAIL",
        re.compile(
            r"\b(?:d[ée]press\w*|anxi[ée]t\w*|psychiatr\w*|psycholog\w*|"
            r"burn[\s-]?out|suicid\w*)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "MEDICAL_SYMPTOM_OR_BIOLOGICAL_DETAIL",
        re.compile(
            r"\b(?:sang|selles?|gastr\w*|naus[ée]\w*|vomiss\w*|douleur\w*|"
            r"fi[èe]vre|sympt[oô]m\w*|l[ée]sion\w*|blessur\w*)\b",
            re.IGNORECASE,
        ),
    ),
)
_COLLECTIVE_SAFETY = re.compile(
    r"\b(?:EPI|[ée]quipement\w*\s+de\s+protection|pr[ée]vention|"
    r"analyse\s+des\s+risques?|mesures?\s+collectives?|plan\s+de\s+pr[ée]vention)\b",
    re.IGNORECASE,
)
_PUBLIC_EVIDENCE_KEYS = {
    "excerpt",
    "raw_excerpt",
    "normalized_excerpt",
    "summary",
    "rule",
    "contribution",
    "apport",
    "qualification_reason",
    "relevance_justification",
    "context_before",
    "context_after",
    "legal_value",
    "limits",
    "limit",
    "employee_argument",
    "employer_argument",
    "employee_interpretation",
    "employer_interpretation",
}


def _clean(value: object) -> str:
    return _SPACE.sub(" ", str(value or "")).strip()


def detect_public_health_categories(value: object) -> tuple[str, ...]:
    text = _clean(value)
    return tuple(name for name, pattern in _HEALTH_PATTERNS if pattern.search(text))


def sanitize_public_evidence_text(
    value: object,
    *,
    preserve_generic_health_context: bool = False,
) -> PublicEvidenceSanitization:
    """Remove individual health detail without maintaining identifying context."""

    text = _clean(value)
    if not text:
        return PublicEvidenceSanitization(None, PublicEvidenceDecision.REJECTED)
    categories = detect_public_health_categories(text)
    if not categories:
        return PublicEvidenceSanitization(text, PublicEvidenceDecision.SAFE)

    retained: list[str] = []
    removed_categories: list[str] = []
    for segment in _SEGMENT.split(text):
        segment = _clean(segment)
        if not segment:
            continue
        segment_categories = detect_public_health_categories(segment)
        if segment_categories:
            removed_categories.extend(segment_categories)
            continue
        retained.append(segment)

    cleaned = _clean(" ".join(retained))
    if cleaned:
        return PublicEvidenceSanitization(
            cleaned,
            PublicEvidenceDecision.GENERALIZED,
            tuple(dict.fromkeys(removed_categories or categories)),
        )
    if preserve_generic_health_context:
        generic = (
            "Des restrictions médicales individuelles sont mentionnées sans détail "
            "identifiable."
            if "FITNESS_OR_MEDICAL_RESTRICTION" in categories
            else "Une situation individuelle de santé est évoquée."
        )
        return PublicEvidenceSanitization(
            generic,
            PublicEvidenceDecision.GENERALIZED,
            categories,
        )
    return PublicEvidenceSanitization(
        None,
        PublicEvidenceDecision.REJECTED,
        categories,
    )


def _sanitize_value(value: Any, *, evidence_context: bool = False) -> Any:
    if isinstance(value, Mapping):
        return sanitize_public_evidence_payload(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        output = [
            _sanitize_value(item, evidence_context=evidence_context)
            for item in value
        ]
        return [item for item in output if item not in (None, "", [], {})]
    if isinstance(value, str) and evidence_context:
        return sanitize_public_evidence_text(value).text
    return value


def _source_identity(value: Mapping[str, Any]) -> tuple[str, str]:
    return (
        _clean(value.get("title") or value.get("source")).casefold(),
        _clean(value.get("reference")).casefold(),
    )


def _deduplicate_summary_evidence(summary: dict[str, Any]) -> dict[str, Any]:
    minutes = [
        dict(item)
        for item in summary.get("cse_context", ())
        if isinstance(item, Mapping)
    ]
    minute_by_identity = {
        _source_identity(item): item
        for item in minutes
        if any(_source_identity(item))
    }
    minute_by_title = {
        title: item
        for (title, _reference), item in minute_by_identity.items()
        if title
    }
    extractions: list[dict[str, Any]] = []
    for raw in summary.get("source_extractions", ()):
        if not isinstance(raw, Mapping):
            continue
        item = dict(raw)
        identity = _source_identity(item)
        minute = minute_by_identity.get(identity) or minute_by_title.get(identity[0])
        if minute is not None:
            contribution = _clean(item.get("link_to_facts"))
            if contribution and not minute.get("contribution"):
                minute["contribution"] = contribution
            item.pop("excerpt", None)
            item["excerpt_reference"] = "Voir le passage CSE/CSSCT présenté une seule fois."
        extractions.append(item)

    for raw in summary.get("rule_to_facts", ()):
        if not isinstance(raw, dict):
            continue
        source = _clean(raw.get("source")).casefold()
        if any(title and title in source for title, _reference in minute_by_identity):
            raw["rule"] = (
                "Passage de PV utilisé comme contexte factuel ; voir l’extrait "
                "CSE/CSSCT présenté une seule fois."
            )
    if "cse_context" in summary:
        summary["cse_context"] = minutes
    if "source_extractions" in summary:
        summary["source_extractions"] = extractions
    return summary


def sanitize_public_evidence_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively sanitize every evidence-bearing public field."""

    output: dict[str, Any] = {}
    evidence_mapping = bool(
        {"source_type", "retrieval_status", "reference", "source"} & set(value)
    )
    for raw_key, item in value.items():
        key = str(raw_key)
        evidence_context = evidence_mapping or key.casefold() in _PUBLIC_EVIDENCE_KEYS
        sanitized = _sanitize_value(item, evidence_context=evidence_context)
        if sanitized not in (None, "", [], {}) or key in {
            "public_summary",
            "detailed_analysis",
        }:
            output[key] = sanitized
    if "public_summary" in output and isinstance(output["public_summary"], dict):
        output["public_summary"] = _deduplicate_summary_evidence(
            output["public_summary"]
        )
    return output


def evidence_remains_useful_after_redaction(value: object) -> bool:
    result = sanitize_public_evidence_text(value)
    return bool(result.text and _COLLECTIVE_SAFETY.search(result.text))


__all__ = (
    "PublicEvidenceDecision",
    "PublicEvidenceSanitization",
    "detect_public_health_categories",
    "evidence_remains_useful_after_redaction",
    "sanitize_public_evidence_payload",
    "sanitize_public_evidence_text",
)
