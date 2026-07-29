"""Public Runtime response boundary.

Internal engines may use storage identifiers, source fingerprints and local
paths while building a response.  This module removes those implementation
details only when the completed payload crosses the user-facing HTTP boundary.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
from typing import Any


_DROP_KEYS = frozenset(
    {
        "_context",
        "cache_path",
        "cache_stale",
        "cache_stored_at",
        "candidate_rank",
        "chunk_id",
        "diagnostic",
        "diagnostics",
        "document_id",
        "employee_id",
        "engine_id",
        "engines",
        "evidence_id",
        "execution_id",
        "file_path",
        "finding_id",
        "fingerprint",
        "hash",
        "internal_id",
        "local_path",
        "metadata_record_id",
        "next_chunk_id",
        "normalized_id",
        "path",
        "plan_id",
        "previous_chunk_id",
        "ranking_reasons",
        "recommendation_id",
        "report_id",
        "request_id",
        "root_path",
        "selection_limits",
        "selection_reasons",
        "source_document_id",
        "source_path",
        "source_relative_path",
        "source_sha256",
        "storage_id",
        "technical_id",
        "technical_reference",
    }
)
_DROP_TOP_LEVEL = frozenset(
    {
        "cse_memory_runtime",
        "official_connectors_runtime",
        "protection_sociale_runtime",
        "retirement_runtime",
        "runtime_integration",
    }
)
_FLOW_LABELS = (
    ("apps/nexus-local-interface/server.py: analyze_question", "Interface Nexus"),
    ("automation/scripts/assistant_ds_router.py: ask --format json", "Routeur Nexus"),
    ("automation/experts/juriste_travail.py: enrich", "Juriste Travail"),
    ("automation/experts/paie.py: enrich", "Expert Paie"),
    (
        "automation/scripts/cdtn_connector.py: search_sources",
        "Code du travail numérique",
    ),
    ("automation/experts/orchestrator.py: orchestrate", "Orchestration experte"),
    ("automation/experts/report_generator.py: build_report", "Rapport Nexus"),
    ("NEXUS_CORE/orchestration: PipelineExecutor", "Nexus Core"),
    (
        "automation/orchestrator_common/orchestrator.py: CommonExpertOrchestrator",
        "Orchestrateur commun",
    ),
    ("NEXUS_RUNTIME_INTEGRATION/cse_memory_runtime.py", "Mémoire CSE"),
    ("NEXUS_RUNTIME_INTEGRATION/retirement_runtime.py", "Retraite et pénibilité"),
    (
        "NEXUS_RUNTIME_INTEGRATION/protection_sociale_runtime.py",
        "Protection sociale",
    ),
)
_ORIGIN_LABELS = {
    "bible_accords": "Accords INEOS",
    "cdtn_pratique_officielle": "Code du travail numérique",
    "judilibre_jurisprudence": "JUDILIBRE",
    "legifrance_code_travail": "Légifrance",
    "nexus_bible_bridge": "Accords INEOS",
    "pratique_officielle": "Code du travail numérique",
}
_SECTION_LABELS = {
    "core_v3_runtime": "analyse_transversale",
    "cse_memory_runtime": "memoire_cse",
    "protection_sociale_runtime": "protection_sociale",
    "retirement_runtime": "retraite_penibilite",
}
_WINDOWS_PATH = re.compile(
    r"(?i)(?<![a-z0-9])(?:file:/+)?[a-z]:[\\/][^|;\r\n)\]]+"
    r"(?=\s+\||[;\r\n)\]]|$)"
)
_POSIX_LOCAL_PATH = re.compile(
    r"(?i)/(?:tmp|home|users)(?:/[^|;\s\r\n)\]]+)+"
)
_UUID = re.compile(
    r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}\b"
)
_LONG_HASH = re.compile(r"(?i)\b[0-9a-f]{32,128}\b")
_RUNTIME_IDENTIFIER = re.compile(r"(?i)\bruntime-[a-z0-9_-]{8,}\b")
_TECHNICAL_REFERENCE = re.compile(
    r"(?i)\b(?:chunk(?:_id)?|storage_id|internal_id|uuid|hash)"
    r"\s*(?:[:=]\s*|\s+)[a-z0-9_.:-]+"
)
_INTERNAL_CORPUS = re.compile(
    r"(?i)\b(?:CCSEMEMORYENGINE|PROTECTION_SOCIALE_ENGINE|LOT_1D)\b"
)
_REDACTED_REFERENCE = "référence interne non publiée"


def sanitize_public_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a user-safe copy without mutating the internal Runtime payload."""

    if not isinstance(payload, Mapping):
        raise TypeError("public Runtime payload must be a mapping")
    public = _sanitize_mapping(payload, top_level=True)
    answer = public.get("answer")
    if isinstance(answer, Mapping) and isinstance(answer.get("case_factual_core"), Mapping):
        return _compact_factual_payload(public)
    return public


def _rows(value: Any, *, limit: int = 8) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return list(value)[:limit]


def _texts(value: Any, *, key: str, limit: int = 8) -> list[str]:
    output: list[str] = []
    for item in _rows(value, limit=limit):
        text = item.get(key) if isinstance(item, Mapping) else item
        if text and str(text) not in output:
            output.append(str(text))
    return output


def _compact_factual_payload(public: Mapping[str, Any]) -> dict[str, Any]:
    """Expose one concise union work sheet instead of every internal engine trace."""

    answer = public["answer"]
    core = answer["case_factual_core"]
    preparation = answer.get("actionable_preparation")
    if not isinstance(preparation, Mapping):
        preparation = {}
    route = answer.get("route")
    if not isinstance(route, Mapping):
        route = {}

    employee_questions = _rows(preparation.get("questions_for_employee"), limit=8)
    employer_questions = _rows(preparation.get("questions_for_employer"), limit=8)
    representative_checks = _rows(preparation.get("representative_checks"), limit=6)
    document_rows = _rows(preparation.get("documents_to_request"), limit=8)
    sources = _rows(answer.get("sources"), limit=8)
    source_layers = []
    for layer in _rows(answer.get("source_layers"), limit=6):
        if not isinstance(layer, Mapping):
            continue
        source_layers.append(
            {
                key: layer.get(key)
                for key in ("id", "label", "status", "absent_message")
                if layer.get(key) not in (None, "")
            }
            | {"sources": _rows(layer.get("sources"), limit=4)}
        )
    warnings = _texts(answer.get("warnings"), key="message", limit=6)
    if not warnings:
        warnings = [str(item) for item in _rows(answer.get("warnings"), limit=6)]

    route_public = {
        key: route.get(key)
        for key in (
            "employee_path",
            "domains",
            "intents",
            "search_query",
            "analysis_suspended",
        )
        if route.get(key) not in (None, [], "")
    }
    compact_answer = {
        "query": answer.get("query"),
        "confidence": answer.get("confidence"),
        "route": route_public,
        "case_factual_core": core,
        "actionable_preparation": {
            "questions_for_employee": employee_questions,
            "questions_for_employer": employer_questions,
            "documents_to_request": document_rows,
            "representative_checks": representative_checks,
        },
        "syndical_position": answer.get("syndical_position", {}),
        "short_answer": answer.get("short_answer"),
        "working_position": answer.get("working_position"),
        "next_action": answer.get("next_action"),
        "findings": _rows(answer.get("findings"), limit=6),
        "documents_to_request": _texts(document_rows, key="document", limit=8),
        "questions_to_ask": [
            *_texts(employee_questions, key="question", limit=8),
            *_texts(employer_questions, key="question", limit=8),
        ][:12],
        "sources": sources,
        "source_layers": source_layers,
        "warnings": warnings,
        "issue_groups": [],
    }
    if answer.get("disciplinary_assistance"):
        discipline = answer["disciplinary_assistance"]
        compact_answer["disciplinary_assistance"] = {
            key: discipline.get(key)
            for key in (
                "1_situation_understood",
                "1_facts_understood",
                "2_points_to_verify",
                "3_provisional_qualification",
                "4_real_disciplinary_risk",
                "5_main_defense_line",
                "6_questions_for_employee",
                "7_questions_for_management",
                "8_interview_preparation",
                "9_points_not_to_say",
                "10_after_interview",
            )
            if discipline.get(key) not in (None, [], {})
        }

    domains = _rows(route.get("domains"), limit=6)
    experts = ["Juriste droit du travail"]
    if "paie_remuneration" in domains:
        experts.append("Expert Paie")
    orchestration = {
        "question_posee": answer.get("query"),
        "domaines_detectes": domains,
        "experts_mobilises": experts,
        "niveau_de_confiance": answer.get("confidence"),
        "reponse_synthetique_nexus": answer.get("short_answer"),
        "position_de_travail": answer.get("working_position"),
        "documents_necessaires": compact_answer["documents_to_request"],
        "questions_utiles": compact_answer["questions_to_ask"],
        "limites": warnings,
        "source_layers": compact_answer["source_layers"],
    }
    juriste = {
        "active": True,
        "response_courte": answer.get("short_answer"),
        "qualification_juridique_situation": [core.get("primary_grievance_or_decision")],
        "ce_qui_est_etabli_par_sources": [
            *_rows(core.get("facts_certain"), limit=5),
            *_rows(core.get("facts_admitted"), limit=4),
        ][:7],
        "ce_qui_depend_accord_statut_element_manquant": [
            *_rows(core.get("facts_missing"), limit=5),
            *_rows(core.get("blocking_ambiguities"), limit=3),
        ][:7],
        "analyse_et_raisonnement": compact_answer["findings"],
        "risques_points_vigilance": _rows(core.get("forbidden_inferences"), limit=5),
        "position_de_travail_proposee": answer.get("working_position"),
        "questions_a_poser_direction": _texts(
            employer_questions, key="question", limit=8
        ),
        "limites": warnings,
    }
    sections = [
        {"title": "Compréhension factuelle", "items": compact_answer["findings"]},
        {
            "title": "Questions prioritaires au salarié",
            "items": _texts(employee_questions, key="question", limit=8),
        },
        {
            "title": "Questions à la direction",
            "items": _texts(employer_questions, key="question", limit=8),
        },
        {"title": "Documents à obtenir", "items": compact_answer["documents_to_request"]},
        {"title": "Position de travail", "items": [answer.get("working_position")]},
        {"title": "Limites", "items": warnings},
    ]
    markdown_parts = [f"# {core.get('primary_grievance_or_decision', 'Analyse Nexus')}"]
    for section in sections:
        markdown_parts.append(f"\n## {section['title']}")
        markdown_parts.extend(
            f"- {item}" for item in section["items"] if item not in (None, "")
        )
    report = {
        "version": "2.3",
        "title": "Fiche de travail syndicale Nexus",
        "generated_from": ["Interface Nexus", "Routeur Nexus", "Juriste Travail"],
        "sections": sections,
        "expert_sections": {"juriste": [], "paie": []},
        "markdown": "\n".join(markdown_parts),
    }
    runtime = public.get("final_assistant_runtime")
    runtime_mode = runtime.get("mode") if isinstance(runtime, Mapping) else "DISABLED"
    return {
        "ok": public.get("ok", True),
        "answer": compact_answer,
        "orchestration": orchestration,
        "expert_juriste": juriste,
        "expert_paie": {"active": False},
        "analysis_report": report,
        "final_assistant_runtime": {"mode": runtime_mode, "assistant": None},
    }


def _sanitize_mapping(value: Mapping[str, Any], *, top_level: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for raw_key, item in value.items():
        key = str(raw_key)
        normalized = key.lower()
        if normalized in _DROP_KEYS or (top_level and normalized in _DROP_TOP_LEVEL):
            continue
        if normalized.endswith(("_sha256", "_storage_id", "_internal_id")):
            continue
        if normalized == "generated_from":
            result[key] = _public_flow(item)
            continue
        if normalized == "origin" and isinstance(item, str):
            result[key] = _ORIGIN_LABELS.get(item, _sanitize_text(item))
            continue
        if normalized == "id" and isinstance(item, str):
            result[key] = _SECTION_LABELS.get(item, _sanitize_text(item))
            continue
        result[key] = _sanitize_value(item)
    return result


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _sanitize_mapping(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str):
        return _sanitize_text(value)
    return value


def _public_flow(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    labels: list[str] = []
    for item in value:
        text = str(item)
        label = next((public for internal, public in _FLOW_LABELS if internal in text), None)
        if label and label not in labels:
            labels.append(label)
    return labels


def _sanitize_text(value: str) -> str:
    text = value
    for internal, public in _FLOW_LABELS:
        text = text.replace(internal, public)
    for internal, public in _ORIGIN_LABELS.items():
        text = text.replace(internal, public)
    text = _INTERNAL_CORPUS.sub("corpus local", text)
    text = _WINDOWS_PATH.sub(_REDACTED_REFERENCE, text)
    text = _POSIX_LOCAL_PATH.sub(_REDACTED_REFERENCE, text)
    text = _UUID.sub(_REDACTED_REFERENCE, text)
    text = _LONG_HASH.sub(_REDACTED_REFERENCE, text)
    text = _RUNTIME_IDENTIFIER.sub(_REDACTED_REFERENCE, text)
    text = _TECHNICAL_REFERENCE.sub(_REDACTED_REFERENCE, text)
    text = re.sub(r"\s+\|\s+\|", " | ", text)
    return text.strip()
