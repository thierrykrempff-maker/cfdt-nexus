#!/usr/bin/env python
"""LOT 4H - Non-calculating integration of payroll business referentials.

The integration reads validated synthetic catalogs to suggest control paths.
It never reads a synthetic value, never computes a result and never treats a
referential item as evidence.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from . import payroll_reasoning_protocol as protocol
from . import payroll_referential_validator as referential_validator


ANALYSIS_DISCLAIMER = (
    "Pistes synthetiques a controler: elles ne remplacent ni les accords, ni la convention collective, "
    "ni le Code du travail, ni les documents reels."
)
MAX_ITEMS = 12

DOCUMENT_ALIASES: Mapping[protocol.DocumentCategory, tuple[str, ...]] = {
    protocol.DocumentCategory.AGREEMENT: ("accord", "accord_entreprise", "accord entreprise"),
    protocol.DocumentCategory.COLLECTIVE_AGREEMENT: ("convention", "convention_collective"),
    protocol.DocumentCategory.LABOUR_CODE: ("code du travail", "code_travail"),
    protocol.DocumentCategory.KELIO: ("kelio", "planning", "pointage", "releve horaire", "compteur"),
    protocol.DocumentCategory.NIBELIS: ("nibelis", "detail de paie", "recapitulatif paie"),
    protocol.DocumentCategory.PAYSLIP: ("bulletin", "bulletin_de_paie", "bulletin de paie"),
    protocol.DocumentCategory.HR_LETTER: ("courrier rh", "notification rh", "arret de travail"),
    protocol.DocumentCategory.MANAGER_DECISION: ("decision manager", "validation manager", "reponse_hierarchie"),
}

SUBJECT_BY_TOPIC: Mapping[str, str] = {
    "heures_supplementaires": "heures_supplementaires",
    "conges_payes": "conges_payes",
    "absence_maladie": "absence",
    "maladie": "absence",
    "prime": "prime",
    "treizieme_mois": "prime",
    "temps_de_travail": "temps_de_travail",
    "nuit": "temps_de_travail",
    "dimanche": "temps_de_travail",
    "jour_ferie": "temps_de_travail",
    "astreinte": "temps_de_travail",
}


def _strings(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set, frozenset)):
        return [str(item) for item in value if str(item or "").strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _unique(values: Iterable[str], limit: int = MAX_ITEMS) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
        if len(result) >= limit:
            break
    return tuple(result)


def identify_subject(topics: Iterable[str], query: str) -> str:
    for topic in topics:
        if topic in SUBJECT_BY_TOPIC:
            return SUBJECT_BY_TOPIC[topic]
    lowered = query.lower()
    keyword_subjects = (
        (("heure supplementaire", "heures supplementaires"), "heures_supplementaires"),
        (("conge",), "conges_payes"),
        (("maladie", "absence"), "absence"),
        (("prime", "13e mois", "treizieme mois"), "prime"),
        (("nuit", "dimanche", "jour ferie", "astreinte", "planning"), "temps_de_travail"),
    )
    for keywords, subject in keyword_subjects:
        if any(keyword in lowered for keyword in keywords):
            return subject
    return "general"


def available_document_categories(answer: Mapping[str, Any], context: Mapping[str, Any]) -> frozenset[protocol.DocumentCategory]:
    raw: list[str] = []
    for key in ("documents", "documents_present", "pieces_presentes"):
        raw.extend(_strings(context.get(key)))
        raw.extend(_strings(answer.get(key)))
    sources = answer.get("sources")
    if isinstance(sources, list):
        for source in sources:
            if isinstance(source, dict):
                raw.extend(str(source.get(key, "")) for key in ("document", "source_layer", "source_layer_label"))
            else:
                raw.append(str(source))
    text = " ".join(raw).lower().replace("-", "_")
    found = {
        category
        for category, aliases in DOCUMENT_ALIASES.items()
        if any(alias in text or alias.replace(" ", "_") in text for alias in aliases)
    }
    if raw and not found:
        found.add(protocol.DocumentCategory.OTHER)
    return frozenset(found)


def _safe_records(catalog: Mapping[str, Any], record_key: str) -> list[dict[str, Any]]:
    records = catalog.get(record_key)
    if not isinstance(records, list):
        return []
    return [
        record
        for record in records
        if isinstance(record, dict)
        and record.get("synthetic_only") is True
        and record.get("calculation_allowed") is False
    ]


def load_safe_catalogs() -> dict[str, dict[str, Any]]:
    catalogs: dict[str, dict[str, Any]] = {}
    for kind in ("kelio", "nibelis", "parameters", "knowledge_graph"):
        report = referential_validator.validate_catalog(kind)
        if report.get("valid") is not True:
            raise ValueError(f"referentiel {kind} invalide")
        catalogs[kind] = referential_validator.load_catalog(kind)
    return catalogs


def _connected_graph_objects(relations: list[dict[str, Any]], starting_rule_ids: set[str]) -> tuple[set[tuple[str, str]], list[dict[str, Any]]]:
    known: set[tuple[str, str]] = {("rule", rule_id) for rule_id in starting_rule_ids}
    selected: list[dict[str, Any]] = []
    changed = True
    while changed:
        changed = False
        for relation in relations:
            left = (str(relation.get("source_type")), str(relation.get("source_id")))
            right = (str(relation.get("target_type")), str(relation.get("target_id")))
            if left in known or right in known:
                if relation not in selected:
                    selected.append(relation)
                for node in (left, right):
                    if node not in known:
                        known.add(node)
                        changed = True
    return known, selected[:MAX_ITEMS]


def _candidate(record: Mapping[str, Any], id_field: str, label_fields: tuple[str, ...]) -> dict[str, Any]:
    label = next((record.get(field) for field in label_fields if record.get(field)), record.get(id_field))
    return {
        "id": str(record.get(id_field)),
        "label": str(label),
        "status": "synthetic_control_hint",
        "calculation_allowed": False,
        "warning": "Indice synthetique a verifier sur les documents reels.",
    }


def find_referential_candidates(rule_analysis: Mapping[str, Any], catalogs: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    rules = [item for item in rule_analysis.get("selected_rules", []) if isinstance(item, dict)]
    rule_ids = {str(item.get("rule_id")) for item in rules if item.get("rule_id")}
    graph_records = _safe_records(catalogs["knowledge_graph"], "relations")
    nodes, relations = _connected_graph_objects(graph_records, rule_ids)

    def selected_records(kind: str, key: str, id_field: str, object_type: str) -> list[dict[str, Any]]:
        records = _safe_records(catalogs[kind], key)
        return [
            record for record in records
            if (object_type, str(record.get(id_field))) in nodes
            or bool(rule_ids.intersection(_strings(record.get("linked_rule_ids"))))
        ][:MAX_ITEMS]

    counters = selected_records("kelio", "counters", "counter_id", "kelio_counter")
    rubrics = selected_records("nibelis", "rubrics", "rubric_id", "nibelis_rubric")
    parameters = selected_records("parameters", "parameters", "parameter_id", "payroll_parameter")
    graph_variables = [node_id for node_type, node_id in nodes if node_type == "variable"]
    rule_variables = [variable for rule in rules for variable in _strings(rule.get("required_variables"))]
    return {
        "rules": [
            {
                "id": str(rule.get("rule_id")),
                "label": str(rule.get("title") or rule.get("rule_id")),
                "status": "rule_to_verify",
                "warning": "Regle a confirmer dans sa source applicable.",
            }
            for rule in rules[:MAX_ITEMS]
        ],
        "variables": _unique((*rule_variables, *graph_variables)),
        "kelio_counters": [_candidate(item, "counter_id", ("label", "counter_code")) for item in counters],
        "nibelis_rubrics": [_candidate(item, "rubric_id", ("label", "rubric_code")) for item in rubrics],
        "parameters": [_candidate(item, "parameter_id", ("label", "parameter_code")) for item in parameters],
        "graph_relations": [
            {
                "id": str(item.get("relation_id")),
                "description": str(item.get("description")),
                "relation_type": str(item.get("relation_type")),
                "status": "synthetic_control_hint",
                "calculation_allowed": False,
            }
            for item in relations
        ],
    }


def _ids(items: Any) -> tuple[str, ...]:
    return _unique(str(item.get("id")) for item in items if isinstance(item, dict) and item.get("id"))


def build_analysis(answer: Mapping[str, Any], rule_analysis: Mapping[str, Any]) -> dict[str, Any]:
    """Prepare protocol and audience responses; return a safe fallback on errors."""
    try:
        catalogs = load_safe_catalogs()
        candidates = find_referential_candidates(rule_analysis, catalogs)
        context = answer.get("payroll_rule_context")
        context = context if isinstance(context, dict) else {}
        topics = _strings(rule_analysis.get("query_topics"))
        subject = identify_subject(topics, str(answer.get("query", "")))
        source_names = tuple(
            str(source.get("document") or source.get("title") or source.get("source_layer"))
            for source in answer.get("sources", [])
            if isinstance(source, dict)
        )
        question = protocol.PayrollQuestion(
            question=str(answer.get("query", "")),
            question_type="controle_paie",
            subject=subject,
            scope=protocol.QuestionScope("employee") if context.get("employee_population") else protocol.QuestionScope.COLLECTIVE,
            population=str(context.get("employee_population") or "").strip() or None,
            period=str(context.get("reference_date") or context.get("period") or "").strip() or None,
            payroll_period=str(context.get("payroll_period") or "").strip() or None,
            urgent=bool(answer.get("urgent") or context.get("urgent")),
            available_documents=available_document_categories(answer, context),
            sources=source_names,
            rules=_ids(candidates["rules"]),
            variables=tuple(candidates["variables"]),
            kelio_counters=_ids(candidates["kelio_counters"]),
            nibelis_rubrics=_ids(candidates["nibelis_rubrics"]),
            parameters=_ids(candidates["parameters"]),
            missing_information=tuple(_strings(rule_analysis.get("variables", {}).get("missing")))
            if isinstance(rule_analysis.get("variables"), dict) else (),
            contradictory_documents=bool(context.get("contradictory_documents")),
        )
        assessment = protocol.assess(question)
        employee_response = protocol.render_response(question, assessment, protocol.Audience("employee"))
        expert_response = protocol.render_response(question, assessment, protocol.Audience.EXPERT)
        expert_response.update(
            {
                "rules": candidates["rules"],
                "variables": candidates["variables"],
                "kelio_counters": candidates["kelio_counters"],
                "nibelis_rubrics": candidates["nibelis_rubrics"],
                "parameters": candidates["parameters"],
                "graph_relations": candidates["graph_relations"],
                "documents_verified": assessment.present_documents,
                "documents_missing": assessment.indispensable_missing_documents,
                "disclaimer": ANALYSIS_DISCLAIMER,
            }
        )
        return {
            "available": True,
            "protocol_steps": assessment.steps,
            "subject": subject,
            "interrupted": not assessment.can_conclude,
            "refusal_reasons": [item.reason for item in assessment.refusals],
            "confidence": assessment.confidence.value,
            "confidence_reasons": tuple((*assessment.missing_information, *(item.reason for item in assessment.refusals))),
            "documents_verified": assessment.present_documents,
            "documents_missing": assessment.indispensable_missing_documents,
            "employee_response": employee_response,
            "expert_response": expert_response,
            "referential_candidates": candidates,
            "calculation_performed": False,
            "synthetic_values_used": False,
            "disclaimer": ANALYSIS_DISCLAIMER,
            "warnings": [],
        }
    except Exception as exc:
        return {
            "available": False,
            "protocol_steps": tuple(step.value for step in protocol.PROTOCOL_STEPS),
            "interrupted": True,
            "refusal_reasons": ["Integration referentielle indisponible; analyse historique conservee."],
            "confidence": protocol.ConfidenceLevel.UNKNOWN.value,
            "confidence_reasons": [str(exc)],
            "documents_verified": (),
            "documents_missing": (),
            "employee_response": {
                "audience": "employee",
                "message": "Impossible de conclure avec certitude.",
                "documents_to_provide": (),
                "confidence": protocol.ConfidenceLevel.UNKNOWN.value,
            },
            "expert_response": {"audience": "expert", "limits": (str(exc),), "disclaimer": ANALYSIS_DISCLAIMER},
            "referential_candidates": {},
            "calculation_performed": False,
            "synthetic_values_used": False,
            "disclaimer": ANALYSIS_DISCLAIMER,
            "warnings": [f"Integration LOT 4H indisponible: {exc}"],
        }
