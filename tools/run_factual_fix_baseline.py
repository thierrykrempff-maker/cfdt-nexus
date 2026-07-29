#!/usr/bin/env python
"""Run and evaluate the factual-understanding corrective baseline on 11 cases."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from tools.run_real_business_cases_baseline import (
    DIMENSION_ORDER,
    ROUTE_BY_CASE,
    _load_server_module,
    _validate_assessment,
    build_case_prompt,
    load_fixtures,
    load_rubric,
    sha256,
)
from tools.run_real_business_cases_second_baseline import load_second_fixtures


ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "tests" / "fixtures" / "real_business_cases"
OUTPUT_DIR = CORPUS_DIR / "factual_fix_baseline"
RAW_DIR = OUTPUT_DIR / "raw"
ASSESSMENT_PATH = OUTPUT_DIR / "factual-fix-assessment.json"
RESULTS_PATH = OUTPUT_DIR / "factual-fix-results.json"
REPORT_PATH = OUTPUT_DIR / "FACTUAL-FIX-RESULTS.md"
CONNECTOR_INVENTORY_PATH = OUTPUT_DIR / "connector-usage-inventory.json"
INITIAL_RESULTS_PATH = CORPUS_DIR / "baseline" / "baseline-results.json"
SECOND_RESULTS_PATH = (
    CORPUS_DIR / "second_set" / "baseline" / "second-baseline-results.json"
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_all_fixtures() -> tuple[dict[str, Any], ...]:
    fixtures = (*load_fixtures(), *load_second_fixtures())
    if len(fixtures) != 11 or len({item["case_id"] for item in fixtures}) != 11:
        raise ValueError("The factual-fix baseline requires exactly eleven unique cases.")
    return tuple(sorted(fixtures, key=lambda item: str(item["case_id"])))


def path_for(fixture: Mapping[str, Any]) -> str:
    return str(
        fixture["case_input"].get("requested_path")
        or ROUTE_BY_CASE[str(fixture["case_id"])]
    )


def reduce_factual_response(payload: Mapping[str, Any]) -> dict[str, Any]:
    answer = dict(payload.get("answer") or {})
    route = dict(answer.get("route") or {})
    disciplinary = dict(answer.get("disciplinary_assistance") or {})
    reduced_disciplinary = {
        key: deepcopy(disciplinary[key])
        for key in (
            "fact_extraction",
            "1_facts_understood",
            "3_provisional_qualification",
            "4_real_disciplinary_risk",
            "5_main_defense_line",
        )
        if key in disciplinary
    }
    return {
        "ok": bool(payload.get("ok")),
        "answer": {
            "case_factual_core": deepcopy(answer.get("case_factual_core")),
            "actionable_preparation": deepcopy(answer.get("actionable_preparation")),
            "syndical_position": deepcopy(answer.get("syndical_position")),
            "short_answer": answer.get("short_answer"),
            "findings": deepcopy(answer.get("findings") or []),
            "documents_to_request": deepcopy(
                answer.get("documents_to_request") or []
            ),
            "questions_to_ask": deepcopy(answer.get("questions_to_ask") or []),
            "sources": deepcopy(answer.get("sources") or []),
            "source_layers": deepcopy(answer.get("source_layers") or []),
            "warnings": deepcopy(answer.get("warnings") or []),
            "disciplinary_assistance": reduced_disciplinary or None,
            "route": {
                key: deepcopy(route[key])
                for key in (
                    "employee_path",
                    "functional_intent",
                    "main_domain",
                    "domains",
                    "analysis_suspended",
                    "search_query",
                )
                if key in route
            },
        },
        "final_assistant_mode": (
            dict(payload.get("final_assistant_runtime") or {}).get("mode")
        ),
    }


def run_baseline(*, source_limit: int = 8) -> tuple[Path, ...]:
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = os.pathsep.join(
        item for item in (str(ROOT), existing_pythonpath) if item
    )
    server = _load_server_module()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for fixture in load_all_fixtures():
        case_input = deepcopy(fixture["case_input"])
        prompt = build_case_prompt({"case_input": case_input})
        employee_path = path_for(fixture)
        public = server.analyze_public_question(prompt, source_limit, employee_path)
        reduced = reduce_factual_response(public)
        envelope = {
            "baseline_schema_version": "1.0",
            "benchmark_set": "factual_fix",
            "case_id": fixture["case_id"],
            "fixture_path": fixture["_fixture_path"],
            "employee_path": employee_path,
            "case_input_sha256": sha256(case_input),
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "evaluation_data_exposed_to_nexus": False,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "response_projection": "factual_fix_visible_v1",
            "public_response_size_bytes": len(
                json.dumps(public, ensure_ascii=False).encode("utf-8")
            ),
            "reduced_response_size_bytes": len(
                json.dumps(reduced, ensure_ascii=False).encode("utf-8")
            ),
            "response": reduced,
        }
        output = RAW_DIR / f"{str(fixture['case_id']).lower()}.response.json"
        output.write_text(
            json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        created.append(output)
    return tuple(created)


def evaluate_baseline() -> dict[str, Any]:
    rubric = load_rubric()
    assessment_payload = read_json(ASSESSMENT_PATH)
    assessments = {
        str(item["case_id"]): item for item in assessment_payload.get("cases", ())
    }
    results: list[dict[str, Any]] = []
    size_rows: list[dict[str, int]] = []
    for fixture in load_all_fixtures():
        case_id = str(fixture["case_id"])
        raw_path = RAW_DIR / f"{case_id.lower()}.response.json"
        if not raw_path.exists() or case_id not in assessments:
            raise ValueError(f"Missing raw response or assessment for {case_id}.")
        raw = read_json(raw_path)
        results.append(
            _validate_assessment(
                fixture,
                raw,
                assessments[case_id],
                rubric,
            )
        )
        size_rows.append(
            {
                "public": int(raw["public_response_size_bytes"]),
                "reduced": int(raw["reduced_response_size_bytes"]),
            }
        )
    average = round(sum(item["total_score"] for item in results) / len(results), 2)
    historical_results = [
        *read_json(INITIAL_RESULTS_PATH)["cases"],
        *read_json(SECOND_RESULTS_PATH)["cases"],
    ]
    initial_scores = {
        str(item["case_id"]): int(item["total_score"])
        for item in historical_results
    }
    if set(initial_scores) != {str(item["case_id"]) for item in load_all_fixtures()}:
        raise ValueError("Historical baselines do not cover the same eleven cases.")
    previous_raw_paths = [
        *sorted((CORPUS_DIR / "baseline" / "raw").glob("*.response.json")),
        *sorted(
            (CORPUS_DIR / "second_set" / "baseline" / "raw").glob(
                "*.response.json"
            )
        ),
    ]
    summary = {
        "baseline_schema_version": "1.0",
        "benchmark_set": "factual_fix",
        "case_count": 11,
        "score_average_before": round(sum(initial_scores.values()) / 11, 2),
        "initial_baseline_average": 32.67,
        "second_baseline_average": 25.20,
        "score_average_after": average,
        "score_variation": round(average - sum(initial_scores.values()) / 11, 2),
        "cases_with_factual_understanding_at_least_14": sum(
            item["dimensions"]["factual_understanding"]["score"] >= 14
            for item in results
        ),
        "average_public_response_size_bytes": round(
            sum(item["public"] for item in size_rows) / len(size_rows)
        ),
        "average_reduced_response_size_bytes": round(
            sum(item["reduced"] for item in size_rows) / len(size_rows)
        ),
        "historical_reduced_snapshot_average_bytes": round(
            sum(path.stat().st_size for path in previous_raw_paths)
            / len(previous_raw_paths)
        ),
        "passed_cases": [item["case_id"] for item in results if item["passed"]],
        "failed_cases": [item["case_id"] for item in results if not item["passed"]],
        "cases": [
            {
                **item,
                "score_before": initial_scores[item["case_id"]],
                "score_variation": item["total_score"]
                - initial_scores[item["case_id"]],
            }
            for item in results
        ],
        "transversal": assessment_payload.get("transversal", {}),
    }
    RESULTS_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    REPORT_PATH.write_text(render_markdown(summary), encoding="utf-8")
    return summary


def render_connector_inventory() -> list[str]:
    inventory = read_json(CONNECTOR_INVENTORY_PATH)
    observation = inventory["execution_observation"]
    nature_labels = {
        "MANDATORY_NORM": "norme obligatoire",
        "CASE_LAW": "jurisprudence",
        "OFFICIAL_RECOMMENDATION": "recommandation officielle",
        "PREVENTION_PRACTICE": "pratique de prévention",
        "EDUCATIONAL_GUIDANCE": "source pédagogique",
        "INSTITUTIONAL_CONTEXT": "élément institutionnel de contexte",
        "OFFICIAL_SOCIAL_INFORMATION": "information sociale officielle",
    }
    lines = [
        "",
        "## Inventaire d'utilisation des connecteurs",
        "",
        "État observé pendant le rejeu des onze cas :",
        "",
        f"- runtime officiel appelé : **{str(observation['official_connector_runtime_called']).lower()}** ;",
        f"- résultats officiels exploités : **{observation['official_runtime_results_exploited']}** ;",
        f"- motif : {observation['reason']}",
        "",
        "| Connecteur | Identifiant réel | Disponible / santé | Domaine et nature | Cas attendus | Cas déclenchés | Résultats exploités | Raison de l'absence |",
        "|---|---|---|---|---|---|---:|---|",
    ]
    for item in inventory["connectors"]:
        expected = "/".join(item["expected_cases"]) or "aucun"
        if item.get("expected_condition"):
            expected += f" ({item['expected_condition']})"
        triggered = "/".join(item["triggered_cases"]) or "aucun"
        available = "oui" if item["available"] else "non"
        nature = nature_labels[item["source_nature"]]
        lines.append(
            f"| {item['connector']} | `{item['connector_platform_id']}` "
            f"(`{item['runtime_engine_id']}`) | {available} — {item['health']} | "
            f"{item['domain']} — **{nature}** | {expected} | {triggered} | "
            f"{item['results_exploited']} | {item['absence_reason']} |"
        )
    lines.extend(
        [
            "",
            "Les accords INEOS et les PV CSE/CSSCT sont des **éléments internes de "
            "contexte**, et non des connecteurs officiels. Aucun résultat local n'a "
            "été exploité pendant cette baseline.",
        ]
    )
    return lines


def render_markdown(results: Mapping[str, Any]) -> str:
    lines = [
        "# LOT 1 — compréhension factuelle et questions exploitables",
        "",
        "Comparaison effectuée sur les onze fixtures inchangées avec la grille de 100 points existante.",
        "",
        f"- Moyenne avant : **{results['score_average_before']}/100**",
        f"  (baseline initiale : {results['initial_baseline_average']}/100 ; "
        f"second lot : {results['second_baseline_average']}/100)",
        f"- Moyenne après : **{results['score_average_after']}/100**",
        f"- Variation : **{results['score_variation']:+.2f} points**",
        "- Compréhension factuelle ≥ 14/20 : "
        f"**{results['cases_with_factual_understanding_at_least_14']}/11**",
        "- Taille publique moyenne : "
        f"**{results['average_public_response_size_bytes']} octets**",
        "- Projection brute réduite moyenne : "
        f"**{results['average_reduced_response_size_bytes']} octets**",
        "- Instantanés réduits historiques moyens : "
        f"**{results['historical_reduced_snapshot_average_bytes']} octets**",
        "",
        "## Comparaison cas par cas",
        "",
        "| Cas | Avant | Après | Variation | Faits | Échecs éliminatoires restants |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for item in results["cases"]:
        failures = ", ".join(item["hard_failures"]) or "aucun"
        lines.append(
            f"| {item['case_id']} | {item['score_before']} | "
            f"{item['total_score']} | {item['score_variation']:+d} | "
            f"{item['dimensions']['factual_understanding']['score']}/20 | {failures} |"
        )
    lines.extend(["", "## Constats transversaux", ""])
    for finding in results.get("transversal", {}).get("findings", ()):
        lines.append(f"- {finding}")
    lines.extend(render_connector_inventory())
    lines.extend(
        [
            "",
            "## Limites",
            "",
            "- Les sources disponibles dépendent de la configuration locale et des connecteurs au moment du rejeu.",
            "- Les anciennes baselines et leurs réponses brutes n'ont pas été modifiées.",
            "- L'issue connue et les attentes d'évaluation n'ont jamais été transmises à Nexus.",
            "- Les scores mesurent ce LOT transversal et ne constituent pas une promesse de résultat juridique.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "evaluate"))
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
    results = evaluate_baseline()
    print(
        json.dumps(
            {
                "case_count": results["case_count"],
                "score_average_after": results["score_average_after"],
                "factual_gate": results[
                    "cases_with_factual_understanding_at_least_14"
                ],
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
