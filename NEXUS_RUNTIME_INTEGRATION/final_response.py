"""Deterministic projection of an internal analysis into a concise response."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
from typing import Any


_SPACE = re.compile(r"\s+")
_PRIORITY = {"BLOCKING": 0, "URGENT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def build_final_response(answer: Mapping[str, Any]) -> dict[str, Any]:
    """Build a short public summary without losing the internal analysis."""

    core = _mapping(answer.get("case_factual_core"))
    preparation = _mapping(answer.get("actionable_preparation"))
    position = _mapping(answer.get("syndical_position"))
    discipline = _mapping(answer.get("disciplinary_assistance"))
    suspended = bool(_mapping(answer.get("route")).get("analysis_suspended"))
    suspended = suspended or bool(core.get("blocking_ambiguities"))
    all_questions = _questions(preparation, bounded=False)
    questions = _bounded_questions(all_questions)
    all_documents = _documents(preparation, bounded=False)
    extraction = _mapping(answer.get("source_extraction"))
    all_documents = _resolved_documents(
        all_documents,
        extraction.get("document_resolutions"),
    )
    documents = all_documents[:5]
    comparisons = _comparisons(answer.get("rule_to_facts_analysis"))
    sources = _sources(
        extraction.get("sources")
        or answer.get("applicable_sources")
        or answer.get("sources")
    )

    avoid = _dedupe(
        [
            position.get("do_not_say"),
            *_strings(core.get("forbidden_inferences"), limit=4),
            *_strings(discipline.get("9_points_not_to_say"), limit=3),
        ],
        limit=4,
        width=340,
    )
    strategy = {
        "before": _dedupe(
            [
                *[item["question"] for item in questions if item["priority"] == "BLOCKING"],
                *[f"Obtenir : {item['document']}" for item in documents],
            ],
            limit=5,
            width=320,
        ),
        "during": _dedupe(
            [
                position.get("point_to_challenge"),
                *_strings(discipline.get("8_interview_preparation"), limit=3),
            ],
            limit=5,
            width=340,
        ),
        "position": _dedupe(
            [position.get("point_to_negotiate"), answer.get("working_position")],
            limit=5,
            width=340,
        ),
    }
    wording = {
        "employee": _dedupe(
            _strings(discipline.get("5_main_defense_line"), limit=3)
            + _strings(discipline.get("1_situation_understood"), limit=2),
            limit=3,
            width=340,
        ),
        "representative": _dedupe(
            _strings(discipline.get("7_questions_for_management"), limit=3),
            limit=3,
            width=340,
        ),
        "avoid": avoid[:2],
    }
    situation = _dedupe(
        [
            core.get("primary_event"),
            core.get("employee_position"),
            core.get("employer_position"),
            *_strings(core.get("dates_and_chronology"), limit=2),
        ],
        limit=6,
        width=420,
    )
    strengths = _dedupe_excluding(
        [
            position.get("employee_strength"),
            *_strings(core.get("facts_certain"), limit=2),
            *_strings(core.get("facts_admitted"), limit=1),
        ],
        excluded=situation,
        limit=3,
        width=360,
    )
    weaknesses = _dedupe_excluding(
        [
            position.get("employee_weakness"),
            *_strings(core.get("facts_disputed"), limit=1),
            *_strings(core.get("facts_missing"), limit=2),
        ],
        excluded=(*situation, *strengths),
        limit=3,
        width=360,
    )
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "analysis_suspended": suspended,
        "urgency": _urgency(core, suspended),
        "urgency_reason": _urgency_reason(core, suspended),
        "situation": situation,
        "syndical_position": _dedupe(
            [
                answer.get("short_answer"),
                answer.get("working_position"),
                position.get("point_to_challenge"),
                position.get("point_to_negotiate"),
            ],
            limit=4,
            width=420,
        ),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "priority_questions": questions,
        "documents": documents,
        "rule_to_facts": comparisons[:3],
        "strategy": strategy,
        "useful_wording": wording,
        "avoid": avoid,
        "next_actions": _dedupe(
            [
                answer.get("next_action"),
                *_strings(discipline.get("10_after_interview"), limit=4),
                *[item.get("next_action") for item in comparisons],
            ],
            limit=5,
            width=340,
        ),
        "sources": _compact_public_sources(sources[:5]),
        "source_extractions": sources[:3],
        "limits": _dedupe_excluding(
            [
                *_strings(core.get("blocking_ambiguities"), limit=3),
                *_strings(core.get("legal_ambiguities"), limit=5),
                *_strings(answer.get("missing_source_requirements"), limit=3),
            ],
            excluded=(*situation, *strengths, *weaknesses),
            limit=3,
            width=340,
        ),
    }
    summary["sections"] = _summary_sections(summary)
    all_sources = _sources(
        extraction.get("sources")
        or answer.get("applicable_sources")
        or answer.get("sources"),
        limit=10,
    )
    details = {
        "factual_core": _compact_core(core),
        "questions": all_questions,
        "documents": all_documents,
        "rule_to_facts": comparisons,
        "secondary_sources": all_sources[5:],
        "source_extraction": extraction,
        "source_requirements": _dedupe(
            _strings(answer.get("missing_source_requirements"), limit=8),
            limit=8,
            width=360,
        ),
        "rejected_sources": _compact_rejections(answer.get("rejected_sources")),
        "warnings": _dedupe(
            _strings(answer.get("warnings"), key="message", limit=8)
            or _strings(answer.get("warnings"), limit=8),
            limit=8,
            width=360,
        ),
    }
    return {
        "public_summary": _drop_empty(summary),
        "detailed_analysis": _drop_empty(details),
    }


def summary_markdown(summary: Mapping[str, Any]) -> str:
    """Render only the public summary for copy, print and export."""

    lines = ["# Synthèse opérationnelle Nexus"]
    if summary.get("urgency"):
        lines.extend(("", f"**Urgence : {summary['urgency']}**"))
    for section in _sequence(summary.get("sections")):
        if not isinstance(section, Mapping):
            continue
        items = _sequence(section.get("items"))
        if not items:
            continue
        lines.extend(("", f"## {section.get('title', 'Section')}"))
        lines.extend(
            f"- {_text(item, 220)}"
            for item in items[:2]
            if _text(item, 220)
        )
    return "\n".join(lines)


def _summary_sections(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    strategy = _mapping(summary.get("strategy"))
    wording = _mapping(summary.get("useful_wording"))
    specs = (
        ("situation", "Situation comprise", summary.get("situation")),
        (
            "urgency",
            "Niveau d’urgence",
            [
                f"{summary.get('urgency')} — {summary.get('urgency_reason')}"
            ],
        ),
        ("position", "Position syndicale provisoire", summary.get("syndical_position")),
        (
            "strengths_weaknesses",
            "Points forts et points faibles",
            [
                *[f"Point fort : {item}" for item in _sequence(summary.get("strengths"))],
                *[f"Point faible : {item}" for item in _sequence(summary.get("weaknesses"))],
            ],
        ),
        (
            "questions",
            "Questions prioritaires",
            [
                f"{item['target']} — {item['question']} ({item['reason']})"
                for item in _sequence(summary.get("priority_questions"))
                if isinstance(item, Mapping)
            ],
        ),
        (
            "documents",
            "Documents à obtenir",
            [
                f"{item['document']} — {item['holder']} — {item['utility']} [{item['priority']}]"
                for item in _sequence(summary.get("documents"))
                if isinstance(item, Mapping)
            ],
        ),
        (
            "comparison",
            "Règles comparées aux faits",
            [
                (
                    f"Règle : {item['source']} — {item.get('rule', '')} "
                    f"Salarié : {item.get('employee_argument', '')} "
                    f"Direction : {item.get('employer_argument', '')} "
                    f"Manquant : {'; '.join(item.get('missing_facts', [])[:1])} "
                    f"Conclusion : {item['conclusion']}. Action : {item['next_action']}"
                )
                for item in _sequence(summary.get("rule_to_facts"))
                if isinstance(item, Mapping)
            ],
        ),
        (
            "strategy",
            "Stratégie pratique",
            [
                *[f"Avant : {item}" for item in _sequence(strategy.get("before"))],
                *[f"Pendant : {item}" for item in _sequence(strategy.get("during"))],
                *[f"Position : {item}" for item in _sequence(strategy.get("position"))],
                *[f"Salarié : {item}" for item in _sequence(wording.get("employee"))],
                *[f"Représentant : {item}" for item in _sequence(wording.get("representative"))],
            ][:5],
        ),
        ("avoid", "À éviter", summary.get("avoid")),
        ("after", "Actions à mener ensuite", summary.get("next_actions")),
        (
            "source_extractions",
            "Sources déjà retrouvées",
            [
                " — ".join(
                    part
                    for part in (
                        item.get("provider"),
                        item.get("title"),
                        item.get("reference"),
                        item.get("excerpt"),
                        item.get("availability_status"),
                        item.get("link_to_facts"),
                    )
                    if part
                )
                for item in _sequence(summary.get("source_extractions"))
                if isinstance(item, Mapping)
            ],
        ),
        (
            "sources",
            "Sources réellement mobilisées",
            [
                " — ".join(
                    part
                    for part in (
                        item.get("provider"),
                        item.get("title"),
                        item.get("nature"),
                        item.get("reference"),
                        item.get("link_to_facts"),
                        item.get("scope"),
                    )
                    if part
                )
                for item in _sequence(summary.get("sources"))
                if isinstance(item, Mapping)
            ],
        ),
        (
            "limits",
            "Limites et incertitudes",
            summary.get("limits"),
        ),
    )
    return [
        {"id": identifier, "title": title, "items": list(items)}
        for identifier, title, items in specs
        if _sequence(items)
    ][:12]


def _questions(
    preparation: Mapping[str, Any], *, bounded: bool = True
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for fallback_target, values in (
        ("SALARIÉ", preparation.get("questions_for_employee")),
        ("DIRECTION", preparation.get("questions_for_employer")),
        ("REPRÉSENTANT", preparation.get("representative_checks")),
    ):
        for item in _sequence(values):
            if not isinstance(item, Mapping) or not item.get("question"):
                continue
            rows.append(
                {
                    "target": fallback_target,
                    "question": _text(item.get("question"), 320),
                    "reason": _text(
                        item.get("purpose") or item.get("changes_analysis_if"), 280
                    ),
                    "priority": str(item.get("priority") or "MEDIUM").upper(),
                }
            )
    rows.sort(
        key=lambda item: (
            _PRIORITY.get(item["priority"], 9),
            item["target"],
            item["question"],
        )
    )
    deduplicated = _dedupe_dicts(rows, "question")
    return _bounded_questions(deduplicated) if bounded else deduplicated


def _bounded_questions(rows: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    blocking = [
        item for item in rows if item["priority"] in {"BLOCKING", "URGENT"}
    ][:5]
    important = [
        item for item in rows if item["priority"] not in {"BLOCKING", "URGENT"}
    ][:5]
    return blocking + important


def _documents(
    preparation: Mapping[str, Any], *, bounded: bool = True
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for item in _sequence(preparation.get("documents_to_request")):
        if not isinstance(item, Mapping) or not item.get("document"):
            continue
        output.append(
            {
                "document": _text(item.get("document"), 220),
                "holder": _text(
                    item.get("holder") or "Direction ou salarié selon détention", 180
                ),
                "utility": _text(
                    item.get("purpose") or item.get("confirms_or_rules_out"), 280
                ),
                "priority": str(item.get("priority") or "MEDIUM").upper(),
            }
        )
    output.sort(key=lambda item: (_PRIORITY.get(item["priority"], 9), item["document"]))
    deduplicated = _dedupe_dicts(output, "document")
    return deduplicated[:5] if bounded else deduplicated


def _resolved_documents(
    documents: Sequence[dict[str, str]],
    resolutions: Any,
) -> list[dict[str, str]]:
    """Remove only documents actually found and qualify uncertain versions."""

    by_document = {
        _text(item.get("requested_document"), 220).casefold(): item
        for item in _sequence(resolutions)
        if isinstance(item, Mapping) and item.get("requested_document")
    }
    output: list[dict[str, str]] = []
    for document in documents:
        resolution = by_document.get(document["document"].casefold())
        status = (
            str(resolution.get("availability_status") or "")
            if isinstance(resolution, Mapping)
            else ""
        )
        if status == "FOUND":
            continue
        row = dict(document)
        if status == "FOUND_VERSION_UNCERTAIN":
            row["document"] = "Confirmer la version applicable : " + row["document"]
            row["utility"] = _text(
                resolution.get("message") or row["utility"],
                280,
            )
        elif status == "NEEDS_CLARIFICATION":
            row["document"] = "Clarifier avant recherche : " + row["document"]
        output.append(row)
    return _dedupe_dicts(output, "document")


def _comparisons(value: Any) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in _sequence(value):
        if not isinstance(item, Mapping):
            continue
        output.append(
            {
                "issue": _text(item.get("issue"), 220),
                "source": _text(item.get("source_reference"), 240),
                "rule": _text(item.get("rule_summary"), 240),
                "employee_argument": _text(
                    item.get("employee_interpretation"), 220
                ),
                "employer_argument": _text(
                    item.get("employer_interpretation"), 220
                ),
                "matching_facts": _dedupe(
                    _strings(item.get("facts_matching"), limit=3), limit=3, width=240
                ),
                "missing_facts": _dedupe(
                    _strings(item.get("facts_missing"), limit=3), limit=3, width=240
                ),
                "conclusion": _text(item.get("provisional_conclusion"), 120),
                "next_action": _text(item.get("next_action"), 280),
                "confidence": _text(item.get("confidence"), 80),
            }
        )
    return _dedupe_dicts(output, "source", secondary="issue")[:8]


def _sources(value: Any, *, limit: int = 5) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for item in _sequence(value):
        if not isinstance(item, Mapping):
            continue
        provider = (
            item.get("provider")
            or item.get("source_provider")
            or item.get("official_origin")
            or item.get("origin")
        )
        title = (
            item.get("title")
            or item.get("source_title")
            or item.get("document")
        )
        if not provider and not title:
            continue
        output.append(
            {
                "provider": _text(provider, 120),
                "title": _text(title, 220),
                "reference": _text(item.get("article_or_clause"), 120),
                "nature": _text(item.get("legal_nature") or item.get("document_type"), 120),
                "status": _text(
                    item.get("retrieval_status")
                    or item.get("availability_status")
                    or "DISPONIBLE",
                    100,
                ),
                "scope": _text(
                    item.get("applicability_status")
                    or item.get("scope")
                    or "À vérifier selon les faits",
                    180,
                ),
                "link_to_facts": _text(
                    item.get("link_to_facts") or item.get("employee_argument"),
                    180,
                ),
                "publication_date": _text(item.get("publication_date"), 40),
                "effective_date": _text(item.get("effective_date"), 40),
                "version_date": _text(item.get("version_date"), 40),
                "excerpt": _text(
                    item.get("excerpt") or item.get("precise_excerpt"),
                    480,
                ),
                "location": _text(
                    item.get("location") or item.get("source_location"),
                    160,
                ),
                "confidence": _text(
                    item.get("confidence") or item.get("confidence_level"),
                    80,
                ),
                "availability_status": _text(
                    item.get("availability_status")
                    or item.get("retrieval_status")
                    or "DISPONIBLE",
                    100,
                ),
                "normative_role": _text(item.get("normative_role"), 160),
            }
        )
    return _dedupe_dicts(output, "provider", secondary="title")[:limit]


def _compact_public_sources(
    sources: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    keys = (
        "provider",
        "title",
        "reference",
        "nature",
        "status",
        "scope",
        "link_to_facts",
    )
    return [
        {key: item[key] for key in keys if item.get(key)}
        for item in sources
    ]


def _compact_rejections(value: Any) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for item in _sequence(value)[:8]:
        if isinstance(item, Mapping):
            output.append(
                {
                    "source": _text(item.get("source") or item.get("title"), 220),
                    "reason": _text(
                        item.get("reason") or item.get("rejection_reason"), 280
                    ),
                }
            )
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            parts = list(item)
            output.append(
                {
                    "source": _text(parts[0] if parts else "", 220),
                    "reason": _text(parts[1] if len(parts) > 1 else "", 280),
                }
            )
    return _drop_empty(output)


def _urgency(core: Mapping[str, Any], suspended: bool) -> str:
    if suspended:
        return "INFORMATION INSUFFISANTE"
    text = " ".join(
        _strings(
            [
                core.get("primary_event"),
                core.get("sanction_or_measure_considered"),
                *_sequence(core.get("dates_and_chronology")),
            ]
        )
    ).casefold()
    if any(
        word in text
        for word in ("licenciement", "mise à pied", "entretien", "échéance", "danger")
    ):
        return "ÉLEVÉ"
    if core.get("facts_missing") or core.get("legal_ambiguities"):
        return "MODÉRÉ"
    return "FAIBLE"


def _urgency_reason(core: Mapping[str, Any], suspended: bool) -> str:
    if suspended:
        return "Une ambiguïté ou un document bloquant empêche une analyse juridique fiable."
    text = " ".join(
        _strings(
            [
                core.get("primary_event"),
                core.get("sanction_or_measure_considered"),
                *_sequence(core.get("dates_and_chronology")),
            ]
        )
    ).casefold()
    if any(word in text for word in ("licenciement", "mise à pied", "entretien")):
        return "Une procédure ou une mesure disciplinaire paraît engagée ou imminente."
    if "danger" in text or core.get("health_and_safety_context"):
        return "La situation comporte un enjeu de santé ou de sécurité à traiter rapidement."
    if core.get("facts_missing") or core.get("legal_ambiguities"):
        return "Des faits ou pièces importants restent à obtenir avant de stabiliser la position."
    return "Aucune échéance immédiate n’est établie dans les éléments fournis."


def _compact_core(core: Mapping[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in core.items():
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            cleaned = _dedupe(_strings(value, limit=12), limit=12, width=420)
        elif isinstance(value, (str, bool, int, float)) or value is None:
            cleaned = _text(value, 500) if isinstance(value, str) else value
        else:
            continue
        if cleaned not in (None, "", [], {}):
            output[str(key)] = cleaned
    return output


def _strings(value: Any, *, key: str | None = None, limit: int = 20) -> list[str]:
    if value is None:
        return []
    values = _sequence(value) if not isinstance(value, str) else [value]
    output: list[str] = []
    for item in values[:limit]:
        if key and isinstance(item, Mapping):
            item = item.get(key)
        text = _text(item, 500)
        if text:
            output.append(text)
    return output


def _dedupe(values: Sequence[Any], *, limit: int, width: int) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value, width)
        normalized = _SPACE.sub(" ", text).strip(" .;:").casefold()
        if not normalized or normalized in seen:
            continue
        if any(
            normalized in prior or prior in normalized
            for prior in seen
            if len(prior) > 35
        ):
            continue
        seen.add(normalized)
        output.append(text)
        if len(output) >= limit:
            break
    return output


def _dedupe_excluding(
    values: Sequence[Any],
    *,
    excluded: Sequence[Any],
    limit: int,
    width: int,
) -> list[str]:
    excluded_normalized = {
        _SPACE.sub(" ", _text(value, width)).strip(" .;:").casefold()
        for value in excluded
        if _text(value, width)
    }
    return _dedupe(
        [
            value
            for value in values
            if _SPACE.sub(" ", _text(value, width)).strip(" .;:").casefold()
            not in excluded_normalized
        ],
        limit=limit,
        width=width,
    )


def _dedupe_dicts(
    values: Sequence[dict[str, Any]], key: str, *, secondary: str | None = None
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for value in values:
        identity = (_text(value.get(key), 500).casefold(),)
        if secondary:
            identity += (_text(value.get(secondary), 500).casefold(),)
        if identity in seen:
            continue
        seen.add(identity)
        output.append(value)
    return output


def _drop_empty(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: cleaned
            for key, item in value.items()
            if (cleaned := _drop_empty(item)) not in (None, "", [], {})
        }
    if isinstance(value, list):
        return [
            cleaned
            for item in value
            if (cleaned := _drop_empty(item)) not in (None, "", [], {})
        ]
    return value


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> list[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    return []


def _text(value: Any, width: int) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        for key in ("text", "message", "question", "title", "label"):
            if value.get(key):
                value = value[key]
                break
        else:
            return ""
    text = _SPACE.sub(" ", str(value)).strip()
    if len(text) <= width:
        return text
    shortened = text[: width - 1].rsplit(" ", 1)[0].rstrip(" ,;:")
    return f"{shortened}…"
