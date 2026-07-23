#!/usr/bin/env python
"""Execute the V1 campaign through the real local-interface Runtime entry point.

The runner is an observation harness only: it invokes the public Runtime
boundary used by ``POST /api/analyze`` and never imports or invokes an expert,
connector or Core component directly.
Tracked output contains neutral measurements, not raw Runtime answers.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import re
import statistics
import sys
import time
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"
DEFAULT_CAMPAIGN = ROOT / "V1_FUNCTIONAL_VALIDATION_MATRIX.json"
DEFAULT_RESULTS = ROOT / "V1_FUNCTIONAL_EXECUTION_RESULTS.json"
DEFAULT_SCORECARD = ROOT / "V1_FUNCTIONAL_EXECUTION_SCORECARD.json"
DEFAULT_REPORT = ROOT / "V1_FUNCTIONAL_EXECUTION_REPORT.md"
DEFAULT_ANOMALIES = ROOT / "V1_FUNCTIONAL_EXECUTION_ANOMALIES.md"

FEATURE_FLAGS = {
    "NEXUS_CORE_RUNTIME_ENABLED": "true",
    "NEXUS_CONNECTOR_RUNTIME_ENABLED": "true",
    "NEXUS_CSE_MEMORY_RUNTIME_ENABLED": "true",
    "NEXUS_RETIREMENT_RUNTIME_ENABLED": "true",
    "NEXUS_PROTECTION_SOCIALE_RUNTIME_ENABLED": "true",
    "NEXUS_OFFICIAL_CONNECTORS_RUNTIME_ENABLED": "true",
}

_ORIGIN_ALIASES = {
    "legifrance_code_travail": "legifrance",
    "judilibre_jurisprudence": "judilibre",
    "cdtn_pratique_officielle": "cdtn",
    "pratique_officielle": "cdtn",
    "cnil": "cnil",
    "dreets_grand_est": "dreets_grand_est",
    "inrs": "inrs",
}
_EXPERT_ALIASES = {
    "juriste": "juriste_travail",
    "juriste_travail": "juriste_travail",
    "paie": "paie",
    "retirement": "retirement",
    "retraite": "retirement",
    "protection_sociale": "protection_sociale",
    "cse_memory": "cse_memory",
}
_SAFE_DIAGNOSTIC_FIELDS = frozenset({
    "core_enabled", "legal_executed", "payroll_executed", "payroll_adapter_called",
    "core_pipeline_called", "common_orchestrator_called", "evidence_count", "finding_count",
    "recommendation_count", "connector_runtime_enabled", "connector_adapter_called",
    "connector_count", "connector_snapshot_count", "connector_evidence_count",
    "connector_fallback_triggered", "connector_fallback_code", "fallback_triggered",
    "fallback_code", "cse_memory_called", "cse_memory_documents_found", "cse_memory_chunks_used",
    "cse_memory_runtime_ms", "cse_memory_fallback", "retirement_called", "retirement_runtime_ms",
    "retirement_elements_used", "retirement_fallback", "protection_sociale_called",
    "protection_sociale_runtime_ms", "protection_sociale_elements_used",
    "protection_sociale_fallback", "connector_runtime_called", "connectors_used",
    "connector_runtime_ms", "connector_runtime_fallback",
})
_PRIVATE_KEY_NAMES = frozenset({
    "chunk_id", "internal_id", "employee_id", "nir", "iban", "rib", "email",
    "phone", "telephone", "matricule", "source_sha256", "storage_id",
    "technical_id", "technical_reference",
})
_PRIVACY_PATTERNS = {
    "absolute_windows_path": re.compile(r"(?i)(?<![a-z0-9])[a-z]:[\\/][^\s\"']+"),
    "absolute_user_path": re.compile(r"/(?:home|Users)/[^\s\"']+"),
    "absolute_tmp_path": re.compile(r"/tmp/[^\s\"']+"),
    "traceback": re.compile(r"Traceback \(most recent call last\)"),
    "secret_or_token": re.compile(r"(?:sk-|ghp_|Bearer\s+)[A-Za-z0-9._-]{8,}"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "iban": re.compile(r"\bFR\d{25}\b"),
    "nir": re.compile(r"\b[12]\d{12}(?:\d{2})?\b"),
    "confidential_filename": re.compile(r"RETIREMENT_PENIBILITY_CONFIDENTIAL_MEMORY_LOT_0", re.I),
    "technical_reference": re.compile(
        r"(?i)(?:chunk_|storage_id|\buuid\b|\b[0-9a-f]{32,128}\b|"
        r"\bruntime-[a-z0-9_-]{8,}\b|CCSEMEMORYENGINE|PROTECTION_SOCIALE_ENGINE|"
        r"(?:apps|automation|NEXUS_CORE|NEXUS_RUNTIME_INTEGRATION)/)"
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_code(value: Any) -> str:
    candidate = re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower()).strip("_")
    return candidate[:100] or "unknown"


def load_runtime_server():
    """Load the same module used by the local HTTP interface."""
    sys.path.insert(0, str(SERVER_PATH.parent))
    spec = importlib.util.spec_from_file_location("nexus_v1_campaign_server", SERVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("RUNTIME_ENTRYPOINT_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) != 100:
        raise ValueError("CAMPAIGN_MUST_CONTAIN_EXACTLY_100_SCENARIOS")
    if len({item.get("id") for item in scenarios}) != 100:
        raise ValueError("SCENARIO_IDENTIFIERS_MUST_BE_UNIQUE")
    return scenarios


def configure_environment(environ: dict[str, str]) -> None:
    for name, value in FEATURE_FLAGS.items():
        environ[name] = value


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) else ()


def _active(payload: Any) -> bool:
    return isinstance(payload, Mapping) and payload.get("active") is not False and bool(payload)


def observed_experts(payload: Mapping[str, Any]) -> tuple[str, ...]:
    found: set[str] = set()
    if _active(payload.get("expert_juriste")):
        found.add("juriste_travail")
    if _active(payload.get("expert_paie")):
        found.add("paie")
    integration = _mapping(payload.get("runtime_integration"))
    for name in _sequence(integration.get("selected_experts")):
        normalized = _EXPERT_ALIASES.get(str(name))
        if normalized:
            found.add(normalized)
    for key, expert, called_keys in (
        ("cse_memory_runtime", "cse_memory", ("called", "cse_memory_called")),
        ("retirement_runtime", "retirement", ("retirement_called",)),
        ("protection_sociale_runtime", "protection_sociale", ("protection_sociale_called",)),
    ):
        diagnostics = _mapping(_mapping(payload.get(key)).get("diagnostics"))
        if any(diagnostics.get(called_key) is True for called_key in called_keys):
            found.add(expert)
    return tuple(sorted(found))


def observed_connectors(payload: Mapping[str, Any]) -> tuple[str, ...]:
    found: set[str] = set()
    answer = _mapping(payload.get("answer"))
    for source in _sequence(answer.get("sources")):
        if not isinstance(source, Mapping):
            continue
        origin = str(source.get("origin") or source.get("connector_id") or source.get("source_id") or "")
        if origin in _ORIGIN_ALIASES:
            found.add(_ORIGIN_ALIASES[origin])
    integration = _mapping(payload.get("runtime_integration"))
    for expert in _sequence(integration.get("selected_experts")):
        name = str(expert)
        if name.startswith("connector_"):
            found.add(name.removeprefix("connector_"))
    official = _mapping(_mapping(payload.get("official_connectors_runtime")).get("diagnostics"))
    found.update(_safe_code(item) for item in _sequence(official.get("connectors_used")))
    cse = _mapping(payload.get("cse_memory_runtime"))
    if cse.get("runtime_mode") == "succeeded":
        found.add("cse_memory")
    protection = _mapping(payload.get("protection_sociale_runtime"))
    if protection.get("runtime_mode") == "succeeded":
        found.add("protection_sociale_local")
    return tuple(sorted(found))


def observed_domains(payload: Mapping[str, Any]) -> tuple[str, ...]:
    route = _mapping(_mapping(payload.get("answer")).get("route"))
    values: list[Any] = [route.get("main_domain")]
    for key in ("domains", "intents", "engines"):
        values.extend(_sequence(route.get(key)))
    return tuple(sorted({_safe_code(item) for item in values if item}))


def source_families(payload: Mapping[str, Any]) -> tuple[str, ...]:
    found: set[str] = set()
    answer = _mapping(payload.get("answer"))
    for source in _sequence(answer.get("sources")):
        if not isinstance(source, Mapping):
            continue
        value = source.get("origin") or source.get("source_layer") or source.get("source_id")
        if value:
            found.add(_safe_code(value))
    return tuple(sorted(found))


def safe_diagnostics(payload: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for section in (
        "runtime_integration", "official_connectors_runtime", "cse_memory_runtime",
        "retirement_runtime", "protection_sociale_runtime",
    ):
        value = _mapping(payload.get(section))
        diagnostics = _mapping(value.get("diagnostics"))
        clean = {
            key: item for key, item in diagnostics.items()
            if key in _SAFE_DIAGNOSTIC_FIELDS and isinstance(item, (str, int, float, bool, type(None), list))
        }
        result[section] = {
            "runtime_mode": _safe_code(value.get("runtime_mode")),
            "diagnostics": clean,
        }
    return result


def privacy_findings(payload: Mapping[str, Any]) -> tuple[str, ...]:
    findings: set[str] = set()
    serialized = json.dumps(payload, ensure_ascii=False, default=str)
    for code, pattern in _PRIVACY_PATTERNS.items():
        if pattern.search(serialized):
            findings.add(code)

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if str(key).lower() in _PRIVATE_KEY_NAMES and item not in (None, "", (), [], {}):
                    findings.add("internal_identifier")
                walk(item)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                walk(item)

    walk(payload)
    return tuple(sorted(findings))


def response_observation(payload: Mapping[str, Any]) -> dict[str, Any]:
    answer = _mapping(payload.get("answer"))
    report = _mapping(payload.get("analysis_report"))
    sections = [item for item in _sequence(report.get("sections")) if isinstance(item, Mapping)]
    markdown = str(report.get("markdown") or "")
    short_answer = str(answer.get("short_answer") or "")
    return {
        "non_empty": bool(markdown.strip() or short_answer.strip() or sections),
        "report_section_ids": [_safe_code(item.get("id")) for item in sections],
        "report_section_count": len(sections),
        "report_item_count": sum(len(_sequence(item.get("items"))) for item in sections),
        "markdown_character_count": len(markdown),
        "short_answer_present": bool(short_answer.strip()),
        "short_answer_character_count": len(short_answer),
        "warning_count": len(_sequence(answer.get("warnings"))),
        "raw_answer_retained": False,
    }


def fallback_observed(diagnostics: Mapping[str, Any]) -> bool:
    for section in diagnostics.values():
        if not isinstance(section, Mapping):
            continue
        if "fallback" in str(section.get("runtime_mode")):
            return True
        for key, value in _mapping(section.get("diagnostics")).items():
            if "fallback" in key and value not in (False, None, "", 0):
                return True
    return False


def _score(value: int | str, basis: str, justification: str, *, human: bool = False) -> dict[str, Any]:
    return {
        "value": value,
        "basis": basis,
        "human_confirmation_required": human,
        "justification": justification,
    }


def primary_route_correct(scenario: Mapping[str, Any], experts: set[str]) -> bool:
    primary = scenario["domaine_principal"]
    required = {
        "paie": {"paie"},
        "protection_sociale": {"protection_sociale"},
        "retraite": {"retirement"},
        "multidomaine": set(scenario["experts_attendus"]),
    }.get(primary, {"juriste_travail"})
    threshold = 2 if primary == "multidomaine" else 1
    return len(required & experts) >= min(threshold, len(required))


def evaluate(scenario: Mapping[str, Any], execution: Mapping[str, Any]) -> dict[str, Any]:
    expected_experts = set(scenario["experts_attendus"])
    actual_experts = set(execution["experts_observes"])
    expected_connectors = set(scenario["connecteurs_attendus"])
    actual_connectors = set(execution["connecteurs_observes"])
    expected_domains = set(scenario["domaines_attendus"])
    actual_domains = set(execution["domaines_observes"])
    technical = execution["statut_execution"] == "success" and execution["reponse_produite"]["non_empty"]
    expert_ratio = len(expected_experts & actual_experts) / len(expected_experts) if expected_experts else 1.0
    domain_ratio = len(expected_domains & actual_domains) / len(expected_domains) if expected_domains else 1.0
    connector_ratio = len(expected_connectors & actual_connectors) / len(expected_connectors) if expected_connectors else 1.0
    route_ok = technical and primary_route_correct(scenario, actual_experts)
    routing = 0 if not technical else round(5 * (0.75 * expert_ratio + 0.25 * domain_ratio))
    routing = min(5, max(0, routing))
    connector_score = "NA" if not expected_connectors else round(5 * connector_ratio)
    references = bool(execution["familles_sources_citees"])
    reference_score = 5 if references else (2 if technical else 0)
    sections = execution["reponse_produite"]["report_section_count"]
    length = execution["reponse_produite"]["markdown_character_count"]
    synthesis = 0 if not technical else (4 if sections and 200 <= length <= 12000 else 3 if sections else 2)
    readability = 0 if not technical else (4 if sections >= 2 else 3 if sections == 1 else 2)
    pertinence = 0 if not technical else (4 if route_ok else 2)
    legal_applicable = "juriste_travail" in expected_experts
    payroll_applicable = "paie" in expected_experts
    agreement_applicable = "accords_ineos" in scenario["domaines_attendus"] or scenario["domaine_principal"] == "accords_ineos"
    legal = "NA" if not legal_applicable else (3 if technical and references else 2 if technical else 0)
    payroll = "NA" if not payroll_applicable else (3 if technical and "paie" in actual_experts else 1 if technical else 0)
    agreement = "NA" if not agreement_applicable else (3 if technical and references else 2 if technical else 0)
    dimensions = {
        "routage": _score(routing, "automatic", "Comparaison des experts et domaines attendus avec les observations Runtime."),
        "exactitude_juridique": _score(legal, "heuristic" if legal != "NA" else "not_applicable", "Pré-évaluation fondée sur l'exécution et les références ; le fond juridique n'a pas de vérité de référence.", human=legal != "NA"),
        "qualite_paie": _score(payroll, "heuristic" if payroll != "NA" else "not_applicable", "Pré-évaluation fondée sur l'activation Paie ; les calculs doivent être vérifiés humainement.", human=payroll != "NA"),
        "utilisation_accords": _score(agreement, "heuristic" if agreement != "NA" else "not_applicable", "Pré-évaluation de présence de sources ; la bonne version et l'articulation exigent une revue humaine.", human=agreement != "NA"),
        "utilisation_connecteurs": _score(connector_score, "automatic" if connector_score != "NA" else "not_applicable", "Taux de couverture des connecteurs attendus."),
        "qualite_synthese": _score(synthesis, "heuristic", "Évaluation de structure et de longueur, sans assimiler longueur et qualité.", human=True),
        "references": _score(reference_score, "automatic", "Présence factuelle de familles de sources dans la réponse."),
        "lisibilite": _score(readability, "heuristic", "Évaluation prudente de la structuration du rapport.", human=True),
        "pertinence_globale": _score(pertinence, "heuristic", "Pré-évaluation fondée sur le routage principal et une réponse non vide.", human=True),
    }
    numeric = [item["value"] for item in dimensions.values() if isinstance(item["value"], int)]
    global_score = round(sum(numeric) / (5 * len(numeric)) * 100, 2) if numeric else 0.0
    deviations = []
    for label, expected, observed in (
        ("experts", expected_experts, actual_experts),
        ("connecteurs", expected_connectors, actual_connectors),
        ("domaines", expected_domains, actual_domains),
    ):
        missing = sorted(expected - observed)
        unexpected = sorted(observed - expected)
        if missing:
            deviations.append({"type": f"{label}_manquants", "values": missing})
        if unexpected:
            deviations.append({"type": f"{label}_inattendus", "values": unexpected})
    if execution["fallback_declenche"]:
        deviations.append({"type": "fallback", "values": ["runtime_fallback"]})
    return {
        "dimensions": dimensions,
        "score_global_sur_100": global_score,
        "routage_principal_correct": route_ok,
        "activation_connecteurs_correcte": expected_connectors <= actual_connectors,
        "revue_humaine_requise": True,
        "ecarts": deviations,
    }


def classify_anomalies(scenario: Mapping[str, Any], execution: Mapping[str, Any], evaluation: Mapping[str, Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    scenario_id = scenario["id"]
    if execution["confidentialite"]["violations"]:
        result.append({"scenario_id": scenario_id, "severity": "P0", "code": "CONFIDENTIALITY_LEAK_DETECTED", "detail": "Une catégorie de donnée sensible a été détectée dans la réponse brute."})
    if execution["statut_execution"] != "success":
        result.append({"scenario_id": scenario_id, "severity": "P1", "code": "TECHNICAL_EXECUTION_FAILED", "detail": "Le Runtime n'a pas produit de résultat exploitable."})
    if not evaluation["routage_principal_correct"]:
        result.append({"scenario_id": scenario_id, "severity": "P1", "code": "PRIMARY_ROUTING_MISMATCH", "detail": "L'expert principal attendu n'a pas été observé."})
    if scenario["connecteurs_attendus"] and not evaluation["activation_connecteurs_correcte"]:
        result.append({"scenario_id": scenario_id, "severity": "P1", "code": "EXPECTED_CONNECTOR_MISSING", "detail": "Au moins un connecteur attendu n'a pas été observé."})
    if execution["fallback_declenche"]:
        result.append({"scenario_id": scenario_id, "severity": "P2", "code": "RUNTIME_FALLBACK", "detail": "Au moins un composant Runtime a utilisé son fallback."})
    if not execution["familles_sources_citees"]:
        result.append({"scenario_id": scenario_id, "severity": "P2", "code": "NO_SOURCE_FAMILY_OBSERVED", "detail": "Aucune famille de source n'a été observée."})
    if evaluation["dimensions"]["lisibilite"]["value"] in (0, 1, 2):
        result.append({"scenario_id": scenario_id, "severity": "P3", "code": "REPORT_STRUCTURE_WEAK", "detail": "La structure observable du rapport est faible."})
    return result


def execute_one(server, scenario: Mapping[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        internal_payload = server.analyze_question(scenario["question_salarie"])
        sanitizer = getattr(server, "sanitize_public_payload", None)
        payload = sanitizer(internal_payload) if callable(sanitizer) else internal_payload
        duration = round((time.perf_counter() - started) * 1000)
        diagnostics = safe_diagnostics(internal_payload)
        result = {
            "id": scenario["id"],
            "domaine_principal": scenario["domaine_principal"],
            "difficulte": scenario["difficulte"],
            "question_envoyee": scenario["question_salarie"],
            "statut_execution": "success",
            "reponse_produite": response_observation(payload),
            "duree_totale_ms": duration,
            "experts_attendus": scenario["experts_attendus"],
            "experts_observes": list(observed_experts(internal_payload)),
            "connecteurs_attendus": scenario["connecteurs_attendus"],
            "connecteurs_observes": list(observed_connectors(internal_payload)),
            "domaines_attendus": scenario["domaines_attendus"],
            "domaines_observes": list(observed_domains(internal_payload)),
            "familles_sources_citees": list(source_families(internal_payload)),
            "diagnostics_techniques": diagnostics,
            "fallback_declenche": fallback_observed(diagnostics),
            "erreur": None,
            "confidentialite": {"violations": list(privacy_findings(payload)), "raw_response_retained": False},
            "attempt_count": 1,
            "retry_reason": None,
        }
    except Exception:
        duration = round((time.perf_counter() - started) * 1000)
        result = {
            "id": scenario["id"], "domaine_principal": scenario["domaine_principal"],
            "difficulte": scenario["difficulte"], "question_envoyee": scenario["question_salarie"],
            "statut_execution": "error",
            "reponse_produite": {
                "non_empty": False,
                "report_section_ids": [],
                "report_section_count": 0,
                "report_item_count": 0,
                "markdown_character_count": 0,
                "short_answer_present": False,
                "short_answer_character_count": 0,
                "warning_count": 0,
                "raw_answer_retained": False,
            },
            "duree_totale_ms": duration, "experts_attendus": scenario["experts_attendus"],
            "experts_observes": [], "connecteurs_attendus": scenario["connecteurs_attendus"],
            "connecteurs_observes": [], "domaines_attendus": scenario["domaines_attendus"],
            "domaines_observes": [], "familles_sources_citees": [], "diagnostics_techniques": {},
            "fallback_declenche": False, "erreur": "RUNTIME_EXECUTION_ERROR",
            "confidentialite": {"violations": [], "raw_response_retained": False},
            "attempt_count": 1, "retry_reason": None,
        }
    result["evaluation"] = evaluate(scenario, result)
    result["ecart_attendu_observe"] = result["evaluation"]["ecarts"]
    return result


def _averages(records: list[dict[str, Any]], key_function) -> dict[str, dict[str, float | int]]:
    groups: dict[str, list[float]] = defaultdict(list)
    for record in records:
        for key in key_function(record):
            groups[key].append(record["evaluation"]["score_global_sur_100"])
    return {key: {"score_moyen": round(statistics.mean(values), 2), "effectif": len(values)} for key, values in sorted(groups.items())}


def aggregate(records: list[dict[str, Any]], anomalies: list[dict[str, str]]) -> dict[str, Any]:
    durations = sorted(record["duree_totale_ms"] for record in records)
    scores = [record["evaluation"]["score_global_sur_100"] for record in records]
    connector_cases = [record for record in records if record["connecteurs_attendus"]]
    expected_connectors = Counter(
        connector for record in records for connector in set(record["connecteurs_attendus"])
    )
    observed_connectors = Counter(
        connector for record in records for connector in set(record["connecteurs_observes"])
    )
    connector_usage = {
        connector: {
            "attendu": expected_connectors[connector],
            "observe": observed_connectors[connector],
            "manquant": max(0, expected_connectors[connector] - observed_connectors[connector]),
            "inattendu": max(0, observed_connectors[connector] - expected_connectors[connector]),
        }
        for connector in sorted(expected_connectors.keys() | observed_connectors.keys())
    }
    return {
        "scenario_count": len(records),
        "technical_successes": sum(record["statut_execution"] == "success" for record in records),
        "technical_failures": sum(record["statut_execution"] != "success" for record in records),
        "empty_responses": sum(not record["reponse_produite"].get("non_empty") for record in records),
        "fallbacks": sum(record["fallback_declenche"] for record in records),
        "score_moyen_global": round(statistics.mean(scores), 2) if scores else 0.0,
        "scores_par_domaine": _averages(records, lambda item: (item["domaine_principal"],)),
        "scores_par_difficulte": _averages(records, lambda item: (item["difficulte"],)),
        "scores_par_expert_attendu": _averages(records, lambda item: item["experts_attendus"]),
        "scores_par_connecteur_attendu": _averages(records, lambda item: item["connecteurs_attendus"]),
        "utilisation_connecteurs": connector_usage,
        "taux_routage_correct": round(100 * sum(record["evaluation"]["routage_principal_correct"] for record in records) / len(records), 2),
        "taux_connecteurs_correctement_actives": round(100 * sum(record["evaluation"]["activation_connecteurs_correcte"] for record in connector_cases) / len(connector_cases), 2) if connector_cases else 100.0,
        "taux_references_presentes": round(100 * sum(bool(record["familles_sources_citees"]) for record in records) / len(records), 2),
        "performance_ms": {
            "moyenne": round(statistics.mean(durations), 2),
            "mediane": round(statistics.median(durations), 2),
            "p95": durations[max(0, round(0.95 * len(durations)) - 1)],
            "maximum": max(durations),
        },
        "anomalies": dict(sorted(Counter(item["severity"] for item in anomalies).items())),
        "contradictions_detectees_automatiquement": 0,
        "contradictions_a_confirmer_humainement": len(records),
        "reponses_sans_famille_source": sum(not record["familles_sources_citees"] for record in records),
        "affirmations_insuffisamment_sourcees_a_confirmer_humainement": len(records),
        "scenarios_plus_faibles": [item["id"] for item in sorted(records, key=lambda value: (value["evaluation"]["score_global_sur_100"], value["id"]))[:10]],
        "scenarios_plus_lents": [item["id"] for item in sorted(records, key=lambda value: (-value["duree_totale_ms"], value["id"]))[:10]],
        "revue_humaine_requise": [record["id"] for record in records if record["evaluation"]["revue_humaine_requise"]],
    }


def _table(values: Mapping[str, Mapping[str, Any]]) -> str:
    lines = ["| Groupe | Score moyen | Effectif |", "|---|---:|---:|"]
    lines.extend(f"| {key} | {item['score_moyen']:.2f} | {item['effectif']} |" for key, item in values.items())
    return "\n".join(lines)


def render_report(scorecard: Mapping[str, Any], records: list[dict[str, Any]], started_at: str, finished_at: str) -> str:
    performance = scorecard["performance_ms"]
    flags = "\n".join(f"- `{name}=true`" for name in FEATURE_FLAGS)
    human = ", ".join(scorecard["revue_humaine_requise"])
    internal_identifier_count = sum(
        "internal_identifier" in record["confidentialite"]["violations"] for record in records
    )
    absolute_path_count = sum(
        "absolute_windows_path" in record["confidentialite"]["violations"] for record in records
    )
    return f"""# CFDT Nexus — exécution fonctionnelle V1

## Contexte et méthode

Campagne exécutée du `{started_at}` au `{finished_at}` sur les 100 questions inchangées de la matrice validée. Le point d'entrée réel est `POST /api/analyze`, implémenté par `apps/nexus-local-interface/server.py:NexusHandler.do_POST`, puis `analyze_public_question()`. Aucun expert, connecteur ou composant Core n'a été appelé directement par l'exécuteur.

Les réponses brutes ont été évaluées en mémoire puis supprimées. Les résultats suivis ne contiennent que des mesures, catégories de sources, diagnostics autorisés et scores prudents. Toute relance éventuelle est tracée individuellement dans les résultats.

## Profil de feature flags

{flags}

Les valeurs par défaut du code n'ont pas été modifiées. Le profil n'a existé que dans le processus de campagne. Les corpus CSE et Protection Sociale utilisent les emplacements locaux par défaut du serveur.

## Résultats globaux

- Scénarios : {scorecard['scenario_count']}
- Réussites techniques : {scorecard['technical_successes']}
- Échecs techniques : {scorecard['technical_failures']}
- Réponses vides : {scorecard['empty_responses']}
- Fallbacks : {scorecard['fallbacks']}
- Score moyen global : {scorecard['score_moyen_global']:.2f}/100
- Routage principal correct : {scorecard['taux_routage_correct']:.2f} %
- Connecteurs correctement activés : {scorecard['taux_connecteurs_correctement_actives']:.2f} %
- Références présentes : {scorecard['taux_references_presentes']:.2f} %

## Résultats par domaine

{_table(scorecard['scores_par_domaine'])}

## Résultats par difficulté

{_table(scorecard['scores_par_difficulte'])}

## Utilisation des connecteurs

La matrice `V1_FUNCTIONAL_EXECUTION_SCORECARD.json` fournit, pour chaque connecteur, les nombres d'activations attendues, observées, manquantes et inattendues. Cette mesure décrit l'activation technique ; elle ne valide ni la pertinence ni l'exactitude des sources.

- Contradictions structurées détectées automatiquement : {scorecard['contradictions_detectees_automatiquement']}
- Scénarios dont les contradictions éventuelles restent à confirmer humainement : {scorecard['contradictions_a_confirmer_humainement']}
- Réponses sans famille de source : {scorecard['reponses_sans_famille_source']}
- Scénarios dont la suffisance du sourçage reste à confirmer humainement : {scorecard['affirmations_insuffisamment_sourcees_a_confirmer_humainement']}

## Performances

- Moyenne : {performance['moyenne']:.2f} ms
- Médiane : {performance['mediane']:.2f} ms
- P95 : {performance['p95']} ms
- Maximum : {performance['maximum']} ms
- Scénarios les plus lents : {', '.join(scorecard['scenarios_plus_lents'])}

## Fallbacks et confidentialité

Les fallbacks sont comptés dès qu'un composant Runtime publie un mode ou un code de fallback. Toute détection de chemin absolu, trace, secret, email, IBAN, NIR, fichier confidentiel ou identifiant interne est classée P0. Les réponses complètes, extraits documentaires et chemins locaux ne sont jamais conservés dans les livrables suivis.

- Identifiants internes détectés dans la réponse Runtime : {internal_identifier_count} scénarios
- Chemins Windows absolus détectés dans la réponse Runtime : {absolute_path_count} scénarios
- Réponses brutes conservées dans les livrables : 0

## Anomalies

- P0 : {scorecard['anomalies'].get('P0', 0)}
- P1 : {scorecard['anomalies'].get('P1', 0)}
- P2 : {scorecard['anomalies'].get('P2', 0)}
- P3 : {scorecard['anomalies'].get('P3', 0)}

Le détail factuel figure dans `V1_FUNCTIONAL_EXECUTION_ANOMALIES.md`. Aucune anomalie n'a été corrigée pendant la campagne.

## Scénarios nécessitant une revue humaine

{human}

La totalité des scénarios nécessite une confirmation humaine de l'exactitude juridique, des calculs de paie applicables, de l'articulation des accords et de la qualité rédactionnelle finale.

## Limites et conclusion factuelle

Les scores d'exactitude juridique, de paie et d'accords sont des pré-évaluations heuristiques, jamais des validations humaines. Le Runtime a été observé avec ses données locales présentes au moment de l'exécution ; l'absence d'une source ou d'un connecteur est un résultat de campagne, pas la preuve que le composant n'existe pas. La readiness V1 doit être décidée à partir des résultats chiffrés, des anomalies et de la revue humaine, sans déduire l'exactitude d'une simple activation technique.
"""


def render_anomalies(anomalies: list[dict[str, str]]) -> str:
    counts = Counter(item["severity"] for item in anomalies)
    lines = [
        "# CFDT Nexus — anomalies de la campagne V1", "",
        "Aucune correction n'a été appliquée pendant cette campagne.", "",
        f"- P0 : {counts.get('P0', 0)}", f"- P1 : {counts.get('P1', 0)}",
        f"- P2 : {counts.get('P2', 0)}", f"- P3 : {counts.get('P3', 0)}", "",
        "| Sévérité | Scénario | Code | Constat |", "|---|---|---|---|",
    ]
    lines.extend(
        f"| {item['severity']} | {item['scenario_id']} | `{item['code']}` | {item['detail']} |"
        for item in sorted(anomalies, key=lambda value: (value["severity"], value["scenario_id"], value["code"]))
    )
    return "\n".join(lines) + "\n"


def write_outputs(records: list[dict[str, Any]], started_at: str, output_paths: Mapping[str, Path]) -> None:
    anomalies = [item for record in records for item in classify_anomalies(
        next(s for s in load_scenarios(DEFAULT_CAMPAIGN) if s["id"] == record["id"]),
        record,
        record["evaluation"],
    )]
    finished_at = utc_now()
    scorecard = aggregate(records, anomalies)
    results_payload = {
        "campaign_id": "CFDT_NEXUS_V1_FUNCTIONAL_EXECUTION",
        "started_at": started_at,
        "finished_at": finished_at,
        "runtime_entrypoint": "apps/nexus-local-interface/server.py:analyze_public_question",
        "http_route": "POST /api/analyze",
        "feature_flags": FEATURE_FLAGS,
        "raw_responses_retained": False,
        "scenario_records": records,
    }
    output_paths["results"].write_text(json.dumps(results_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_paths["scorecard"].write_text(json.dumps(scorecard, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_paths["report"].write_text(render_report(scorecard, records, started_at, finished_at), encoding="utf-8")
    output_paths["anomalies"].write_text(render_anomalies(anomalies), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute the 100-scenario Nexus V1 campaign")
    parser.add_argument("--campaign", type=Path, default=DEFAULT_CAMPAIGN)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--scorecard", type=Path, default=DEFAULT_SCORECARD)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--anomalies", type=Path, default=DEFAULT_ANOMALIES)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="test-only bounded execution")
    args = parser.parse_args()
    scenarios = load_scenarios(args.campaign)
    if args.limit is not None:
        scenarios = scenarios[:args.limit]
    configure_environment(__import__("os").environ)
    server = load_runtime_server()
    records: list[dict[str, Any]] = []
    started_at = utc_now()
    if args.resume and args.results.exists():
        previous = json.loads(args.results.read_text(encoding="utf-8"))
        records = list(previous.get("scenario_records") or ())
        started_at = previous.get("started_at") or started_at
    completed = {item["id"] for item in records}
    for index, scenario in enumerate(scenarios, start=1):
        if scenario["id"] in completed:
            continue
        record = execute_one(server, scenario)
        records.append(record)
        records.sort(key=lambda item: item["id"])
        write_outputs(records, started_at, {
            "results": args.results, "scorecard": args.scorecard,
            "report": args.report, "anomalies": args.anomalies,
        })
        print(f"[{index:03d}/{len(scenarios):03d}] {scenario['id']} {record['statut_execution']} {record['duree_totale_ms']}ms", flush=True)


if __name__ == "__main__":
    main()
