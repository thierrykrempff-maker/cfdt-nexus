#!/usr/bin/env python
"""Run and evaluate the anonymized real-business-case Nexus baseline.

The Nexus request is built exclusively from ``case_input``. Evaluator
expectations and known outcomes are loaded only after raw responses exist.
This tool never changes a Nexus engine or its configuration.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "real_business_cases"
RAW_DIR = FIXTURE_DIR / "baseline" / "raw"
ASSESSMENT_PATH = FIXTURE_DIR / "baseline" / "baseline-assessment.json"
RESULTS_PATH = FIXTURE_DIR / "baseline" / "baseline-results.json"
REPORT_PATH = FIXTURE_DIR / "baseline" / "BASELINE.md"
RUBRIC_PATH = FIXTURE_DIR / "scoring-rubric.json"
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"

ROUTE_BY_CASE = {
    "REAL-01-INSULTING_EMAILS_ALCOHOL": "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE",
    "REAL-02-SMOKING_BREAKS_SEVESO_BADGE": "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE",
    "REAL-03-TAG_INSTALLATION": "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE",
    "REAL-04-FORCED_DAY_TO_SHIFT_LABORATORY": "QUESTION_SALARIE",
    "REAL-05-DELEGATION_HOURS_CSSCT_INCOMPLETE": "QUESTION_SALARIE",
    "REAL-06-ANNUAL_LEAVE_TEN_PERCENT_UNRESOLVED": "QUESTION_SALARIE",
}

DIMENSION_ORDER = (
    "factual_understanding",
    "question_relevance",
    "source_relevance",
    "rule_fact_comparison",
    "strategy_realism",
    "adversarial_analysis",
    "no_invention",
    "practical_usefulness",
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_fixtures() -> tuple[dict[str, Any], ...]:
    fixtures: list[dict[str, Any]] = []
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        payload = read_json(path)
        if "case_id" in payload:
            payload["_fixture_path"] = str(path.relative_to(ROOT)).replace("\\", "/")
            fixtures.append(payload)
    identifiers = [item["case_id"] for item in fixtures]
    if set(identifiers) != set(ROUTE_BY_CASE):
        raise ValueError(
            "The baseline requires exactly the six expected case identifiers; "
            f"received {identifiers!r}"
        )
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Case identifiers must be unique.")
    return tuple(sorted(fixtures, key=lambda item: str(item["case_id"])))


def build_case_prompt(fixture: Mapping[str, Any]) -> str:
    """Create the Nexus prompt without reading any evaluator-only field."""

    case_input = deepcopy(dict(fixture["case_input"]))
    headings = (
        ("Faits fournis", "facts_provided"),
        ("Faits reconnus", "facts_recognized"),
        ("Faits contestés", "facts_contested"),
        ("Faits allégués", "facts_alleged"),
        ("Informations manquantes déjà identifiées", "missing_information"),
    )
    lines = [
        "Analyse cette situation syndicale à partir des seuls éléments fournis.",
        "Distingue les faits certains, reconnus, contestés, allégués et manquants.",
        "Pose les questions déterminantes, indique les sources réellement disponibles "
        "ou indisponibles, compare les règles aux faits et n'invente rien.",
    ]
    for label, key in headings:
        lines.extend(["", f"{label} :"])
        values = case_input.get(key) or []
        if not values:
            lines.append("- Aucun élément fourni.")
            continue
        for value in values:
            if isinstance(value, Mapping):
                lines.append(
                    f"- {value.get('item')} "
                    f"[importance: {value.get('importance')}] — {value.get('reason')}"
                )
            else:
                lines.append(f"- {value}")
    return "\n".join(lines)


def _load_server_module():
    module_name = "nexus_local_server_real_business_baseline"
    app_dir = str(SERVER_PATH.parent)
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    spec = importlib.util.spec_from_file_location(module_name, SERVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the Nexus local interface server.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reduce_public_response(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Keep the visible baseline evidence and discard redundant runtime payloads."""

    answer = dict(payload.get("answer") or {})
    reduced_answer = {
        key: deepcopy(answer[key])
        for key in (
            "confidence",
            "actionable_preparation",
            "case_factual_core",
            "disciplinary_assistance",
            "documents_to_request",
            "employee_method_analysis",
            "execution_plan",
            "facts",
            "findings",
            "issue_groups",
            "jurisprudence_audit",
            "legifrance_audit",
            "next_action",
            "query",
            "questions_to_ask",
            "response_depth",
            "route",
            "short_answer",
            "source_layers",
            "sources",
            "syndical_position",
            "understanding",
            "warnings",
            "working_position",
        )
        if key in answer
    }
    orchestration = dict(payload.get("orchestration") or {})
    reduced_orchestration = {
        key: deepcopy(orchestration[key])
        for key in (
            "question_posee",
            "domaines_detectes",
            "experts_mobilises",
            "niveau_de_confiance",
            "reponse_synthetique_nexus",
            "position_de_travail",
            "documents_necessaires",
            "questions_utiles",
            "limites",
            "sources",
        )
        if key in orchestration
    }
    juriste = dict(payload.get("expert_juriste") or {})
    reduced_juriste = {
        key: deepcopy(juriste[key])
        for key in (
            "active",
            "response_courte",
            "qualification_juridique_situation",
            "ce_qui_est_etabli_par_sources",
            "ce_qui_depend_accord_statut_element_manquant",
            "analyse_et_raisonnement",
            "risques_points_vigilance",
            "position_de_travail_proposee",
            "questions_a_poser_direction",
            "limites",
            "action_conseillee",
        )
        if key in juriste
    }
    paie = dict(payload.get("expert_paie") or {})
    reduced_paie = {
        key: deepcopy(paie[key])
        for key in (
            "active",
            "objet_du_controle",
            "elements_du_bulletin_concernes",
            "regles_ou_sources_disponibles",
            "donnees_necessaires_au_calcul",
            "methode_de_controle",
            "anomalies_potentielles",
            "calcul_detaille",
            "documents_necessaires",
            "limites",
        )
        if key in paie
    }
    report = dict(payload.get("analysis_report") or {})
    reduced_report = {
        key: deepcopy(report[key])
        for key in (
            "version",
            "title",
            "generated_from",
            "sections",
            "expert_sections",
        )
        if key in report
    }
    final_runtime = dict(payload.get("final_assistant_runtime") or {})
    syndical_runtime = dict(payload.get("syndical_reasoning_runtime") or {})
    return {
        "ok": bool(payload.get("ok")),
        "answer": reduced_answer,
        "orchestration": reduced_orchestration,
        "expert_juriste": reduced_juriste,
        "expert_paie": reduced_paie,
        "analysis_report": reduced_report,
        "final_assistant_runtime": {
            key: deepcopy(final_runtime[key])
            for key in ("mode", "diagnostics")
            if key in final_runtime
        },
        "syndical_reasoning_runtime": {
            key: deepcopy(syndical_runtime[key])
            for key in ("mode", "diagnostics")
            if key in syndical_runtime
        },
    }


def run_baseline(*, source_limit: int = 8) -> tuple[Path, ...]:
    fixtures = load_fixtures()
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    baseline_pythonpath = [str(ROOT)]
    if existing_pythonpath:
        baseline_pythonpath.append(existing_pythonpath)
    os.environ["PYTHONPATH"] = os.pathsep.join(baseline_pythonpath)
    server = _load_server_module()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for fixture in fixtures:
        case_id = str(fixture["case_id"])
        case_input = deepcopy(fixture["case_input"])
        prompt = build_case_prompt({"case_input": case_input})
        employee_path = ROUTE_BY_CASE[case_id]
        response = server.analyze_public_question(
            prompt,
            source_limit,
            employee_path,
        )
        envelope = {
            "baseline_schema_version": "1.0",
            "case_id": case_id,
            "fixture_path": fixture["_fixture_path"],
            "employee_path": employee_path,
            "case_input_sha256": sha256(case_input),
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "evaluation_data_exposed_to_nexus": False,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "response_projection": "visible_baseline_v1",
            "response": reduce_public_response(response),
        }
        output = RAW_DIR / f"{case_id.lower()}.response.json"
        output.write_text(
            json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        created.append(output)
    return tuple(created)


def compact_existing_raw_responses() -> tuple[Path, ...]:
    updated: list[Path] = []
    for path in sorted(RAW_DIR.glob("*.response.json")):
        envelope = read_json(path)
        envelope["response_projection"] = "visible_baseline_v1"
        envelope["response"] = reduce_public_response(envelope["response"])
        path.write_text(
            json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        updated.append(path)
    if len(updated) != len(ROUTE_BY_CASE):
        raise ValueError("Exactly six raw responses are required for compaction.")
    return tuple(updated)


def load_rubric() -> dict[str, Any]:
    rubric = read_json(RUBRIC_PATH)
    if sum(int(item["max_points"]) for item in rubric["dimensions"]) != 100:
        raise ValueError("Rubric weights must total 100.")
    return rubric


def _dimension_definitions(rubric: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): dict(item) for item in rubric["dimensions"]}


def _validate_assessment(
    fixture: Mapping[str, Any],
    raw: Mapping[str, Any],
    assessment: Mapping[str, Any],
    rubric: Mapping[str, Any],
) -> dict[str, Any]:
    case_id = str(fixture["case_id"])
    if raw.get("case_id") != case_id or assessment.get("case_id") != case_id:
        raise ValueError(f"Case identifier mismatch for {case_id}.")
    if raw.get("case_input_sha256") != sha256(fixture["case_input"]):
        raise ValueError(f"Raw response no longer matches case_input for {case_id}.")
    if raw.get("evaluation_data_exposed_to_nexus") is not False:
        raise ValueError(f"Evaluator data exposure guard failed for {case_id}.")

    definitions = _dimension_definitions(rubric)
    dimensions = assessment.get("dimensions")
    if not isinstance(dimensions, Mapping) or set(dimensions) != set(DIMENSION_ORDER):
        raise ValueError(f"Eight dimension assessments are required for {case_id}.")
    normalized_dimensions: dict[str, Any] = {}
    for identifier in DIMENSION_ORDER:
        entry = dimensions[identifier]
        score = int(entry["score"])
        maximum = int(definitions[identifier]["max_points"])
        if score < 0 or score > maximum:
            raise ValueError(f"Invalid {identifier} score for {case_id}.")
        notes = [str(item) for item in entry.get("evidence", ())]
        if not notes:
            raise ValueError(f"Evidence is required for {identifier} in {case_id}.")
        normalized_dimensions[identifier] = {
            "score": score,
            "max_points": maximum,
            "minimum_to_pass": int(definitions[identifier]["minimum_to_pass"]),
            "evidence": notes,
        }

    known_failure_codes = {str(item["code"]) for item in rubric["hard_failures"]}
    hard_failures = [str(item) for item in assessment.get("hard_failures", ())]
    unknown = set(hard_failures) - known_failure_codes
    if unknown:
        raise ValueError(f"Unknown hard-failure codes for {case_id}: {sorted(unknown)}")
    factual = normalized_dimensions["factual_understanding"]["score"]
    if factual < normalized_dimensions["factual_understanding"]["minimum_to_pass"]:
        if "FACTUAL_MISUNDERSTANDING" not in hard_failures:
            hard_failures.append("FACTUAL_MISUNDERSTANDING")

    below_minimum = [
        identifier
        for identifier, entry in normalized_dimensions.items()
        if entry["score"] < entry["minimum_to_pass"]
    ]
    total = sum(entry["score"] for entry in normalized_dimensions.values())
    passed = not hard_failures and not below_minimum and total >= int(
        rubric["passing_score"]
    )
    return {
        "case_id": case_id,
        "title": fixture["title"],
        "employee_path": raw["employee_path"],
        "total_score": total,
        "maximum_score": 100,
        "passed": passed,
        "dimensions": normalized_dimensions,
        "hard_failures": hard_failures,
        "dimensions_below_minimum": below_minimum,
        "successes": [str(item) for item in assessment.get("successes", ())],
        "errors": [str(item) for item in assessment.get("errors", ())],
        "irrelevant_sources": [
            str(item) for item in assessment.get("irrelevant_sources", ())
        ],
        "invented_facts": [str(item) for item in assessment.get("invented_facts", ())],
        "missing_essential_questions": [
            str(item) for item in assessment.get("missing_essential_questions", ())
        ],
        "unrealistic_strategies": [
            str(item) for item in assessment.get("unrealistic_strategies", ())
        ],
        "important_repetitions": [
            str(item) for item in assessment.get("important_repetitions", ())
        ],
        "correction_priority": str(assessment.get("correction_priority") or ""),
        "known_outcome_used_only_after_core_scoring": True,
    }


def evaluate_baseline() -> dict[str, Any]:
    fixtures = load_fixtures()
    rubric = load_rubric()
    assessment_payload = read_json(ASSESSMENT_PATH)
    assessments = {
        str(item["case_id"]): item for item in assessment_payload.get("cases", ())
    }
    results = []
    for fixture in fixtures:
        case_id = str(fixture["case_id"])
        raw_path = RAW_DIR / f"{case_id.lower()}.response.json"
        if not raw_path.exists():
            raise FileNotFoundError(f"Missing raw response for {case_id}.")
        if case_id not in assessments:
            raise ValueError(f"Missing assessment for {case_id}.")
        results.append(
            _validate_assessment(
                fixture,
                read_json(raw_path),
                assessments[case_id],
                rubric,
            )
        )
    summary = {
        "baseline_schema_version": "1.0",
        "case_count": len(results),
        "score_average": round(
            sum(item["total_score"] for item in results) / len(results), 2
        ),
        "passed_cases": [item["case_id"] for item in results if item["passed"]],
        "failed_cases": [item["case_id"] for item in results if not item["passed"]],
        "cases": results,
        "transversal": assessment_payload.get("transversal", {}),
    }
    RESULTS_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    REPORT_PATH.write_text(render_markdown(summary), encoding="utf-8")
    return summary


def render_markdown(results: Mapping[str, Any]) -> str:
    def append_items(lines: list[str], values: list[str], empty: str) -> None:
        if values:
            lines.extend(f"- {item}" for item in values)
        else:
            lines.append(f"- {empty}")

    lines = [
        "# Baseline Nexus — cas métier réels anonymisés",
        "",
        "Cette baseline mesure le comportement existant de Nexus. Aucun moteur n'a "
        "été modifié pour améliorer les réponses.",
        "",
        f"- Cas exécutés : {results['case_count']}",
        f"- Score moyen : {results['score_average']}/100",
        f"- Cas réussis : {len(results['passed_cases'])}",
        f"- Cas en échec : {len(results['failed_cases'])}",
        "",
        "## Limites de cette mesure",
        "",
        "- L'Assistant Final était désactivé pendant les six exécutions.",
        "- La baseline porte principalement sur le moteur historique et son orchestration.",
        "- La Bible Accords locale était indisponible ou vide.",
        "- La disponibilité des sources officielles a varié selon les cas.",
        "- Les scores ne représentent pas la performance maximale possible de toute "
        "l'architecture Nexus dans une autre configuration.",
        "",
        "## Scores",
        "",
        "| Cas | Faits | Questions | Sources | Texte/faits | Stratégie | Contradictoire | Sans invention | Pratique | Total | Verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for result in results["cases"]:
        scores = result["dimensions"]
        lines.append(
            f"| {result['case_id']} | "
            f"{scores['factual_understanding']['score']}/20 | "
            f"{scores['question_relevance']['score']}/10 | "
            f"{scores['source_relevance']['score']}/15 | "
            f"{scores['rule_fact_comparison']['score']}/15 | "
            f"{scores['strategy_realism']['score']}/15 | "
            f"{scores['adversarial_analysis']['score']}/10 | "
            f"{scores['no_invention']['score']}/10 | "
            f"{scores['practical_usefulness']['score']}/5 | "
            f"**{result['total_score']}/100** | "
            f"{'RÉUSSI' if result['passed'] else 'ÉCHEC'} |"
        )
    for result in results["cases"]:
        lines.extend(
            [
                "",
                f"## {result['case_id']} — {result['title']}",
                "",
                f"- Parcours : `{result['employee_path']}`",
                f"- Score : **{result['total_score']}/100**",
                "- Règles éliminatoires : "
                + (
                    ", ".join(f"`{item}`" for item in result["hard_failures"])
                    if result["hard_failures"]
                    else "aucune"
                ),
                f"- Priorité de correction : {result['correction_priority']}",
                "",
                "### Réussites",
                "",
            ]
        )
        append_items(lines, result["successes"], "Aucune réussite notable.")
        lines.extend(["", "### Erreurs", ""])
        append_items(lines, result["errors"], "Aucune erreur notable.")
        for title, key in (
            ("Sources hors sujet", "irrelevant_sources"),
            ("Faits inventés", "invented_facts"),
            ("Questions essentielles absentes", "missing_essential_questions"),
            ("Stratégies irréalistes", "unrealistic_strategies"),
            ("Répétitions importantes", "important_repetitions"),
        ):
            lines.extend(["", f"### {title}", ""])
            values = result[key]
            append_items(lines, values, "Aucune.")
    transversal = results.get("transversal") or {}
    lines.extend(["", "## Synthèse transversale", ""])
    for label, key in (
        ("Erreurs récurrentes de compréhension", "recurring_understanding_errors"),
        ("Fausses pistes récurrentes", "recurring_false_leads"),
        ("Sélection documentaire", "document_selection_problems"),
        ("Jurisprudence", "jurisprudence_problems"),
        ("Stratégie", "strategy_problems"),
        ("Interface et restitution", "interface_or_rendering_problems"),
        ("Familles les plus faibles", "weakest_case_families"),
        ("Trois corrections prioritaires maximales", "top_three_priorities"),
    ):
        lines.extend([f"### {label}", ""])
        values = [str(item) for item in transversal.get(key, ())]
        append_items(lines, values, "Aucun élément.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "compact", "evaluate"))
    parser.add_argument("--source-limit", type=int, default=8)
    args = parser.parse_args()
    if args.command == "run":
        paths = run_baseline(source_limit=args.source_limit)
        print(
            json.dumps(
                {"raw_responses": [str(path.relative_to(ROOT)) for path in paths]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "compact":
        paths = compact_existing_raw_responses()
        print(
            json.dumps(
                {
                    "compacted_raw_responses": [
                        str(path.relative_to(ROOT)) for path in paths
                    ]
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    results = evaluate_baseline()
    print(
        json.dumps(
            {
                "case_count": results["case_count"],
                "score_average": results["score_average"],
                "passed_cases": results["passed_cases"],
                "failed_cases": results["failed_cases"],
                "results": str(RESULTS_PATH.relative_to(ROOT)),
                "report": str(REPORT_PATH.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
