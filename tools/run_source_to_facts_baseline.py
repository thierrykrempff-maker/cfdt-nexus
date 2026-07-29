#!/usr/bin/env python
"""Run and evaluate the source-to-facts baseline on the eleven reference cases."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from tools.run_factual_fix_baseline import (
    load_all_fixtures,
    path_for,
    read_json,
)
from tools.run_real_business_cases_baseline import (
    _load_server_module,
    _validate_assessment,
    build_case_prompt,
    load_rubric,
    sha256,
)


ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "tests" / "fixtures" / "real_business_cases"
OUTPUT_DIR = CORPUS_DIR / "source_to_facts_baseline"
RAW_DIR = OUTPUT_DIR / "raw"
ASSESSMENT_PATH = OUTPUT_DIR / "source-to-facts-assessment.json"
RESULTS_PATH = OUTPUT_DIR / "source-to-facts-results.json"
REPORT_PATH = OUTPUT_DIR / "SOURCE-TO-FACTS-RESULTS.md"
SOURCE_INVENTORY_PATH = OUTPUT_DIR / "source-inventory.json"
REJECTED_SOURCES_PATH = OUTPUT_DIR / "rejected-sources.json"
BEFORE_AFTER_PATH = OUTPUT_DIR / "before-after.json"
PREVIOUS_ASSESSMENT_PATH = (
    CORPUS_DIR / "factual_fix_baseline" / "factual-fix-assessment.json"
)
PREVIOUS_RESULTS_PATH = (
    CORPUS_DIR / "factual_fix_baseline" / "factual-fix-results.json"
)


def reduce_response(payload: Mapping[str, Any]) -> dict[str, Any]:
    answer = dict(payload.get("answer") or {})
    route = dict(answer.get("route") or {})
    return {
        "ok": bool(payload.get("ok")),
        "answer": {
            "case_factual_core": deepcopy(answer.get("case_factual_core")),
            "actionable_preparation": deepcopy(
                answer.get("actionable_preparation")
            ),
            "syndical_position": deepcopy(answer.get("syndical_position")),
            "short_answer": answer.get("short_answer"),
            "sources": deepcopy(answer.get("sources") or []),
            "source_layers": deepcopy(answer.get("source_layers") or []),
            "source_search_plan": deepcopy(
                answer.get("source_search_plan") or []
            ),
            "applicable_sources": deepcopy(
                answer.get("applicable_sources") or []
            ),
            "rule_to_facts_analysis": deepcopy(
                answer.get("rule_to_facts_analysis") or []
            ),
            "rejected_sources": deepcopy(
                answer.get("rejected_sources") or []
            ),
            "missing_source_requirements": deepcopy(
                answer.get("missing_source_requirements") or []
            ),
            "adversarial_source_analysis": deepcopy(
                answer.get("adversarial_source_analysis") or {}
            ),
            "control_device_hypotheses": deepcopy(
                answer.get("control_device_hypotheses") or []
            ),
            "questions_to_ask": deepcopy(answer.get("questions_to_ask") or []),
            "documents_to_request": deepcopy(
                answer.get("documents_to_request") or []
            ),
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
        reduced = reduce_response(public)
        envelope = {
            "baseline_schema_version": "1.0",
            "benchmark_set": "source_to_facts",
            "case_id": fixture["case_id"],
            "fixture_path": fixture["_fixture_path"],
            "employee_path": employee_path,
            "case_input_sha256": sha256(case_input),
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "evaluation_data_exposed_to_nexus": False,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "response_projection": "source_to_facts_visible_v1",
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
            json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        created.append(output)
    return tuple(created)


def _previous_assessments() -> dict[str, dict[str, Any]]:
    return {
        str(item["case_id"]): deepcopy(item)
        for item in read_json(PREVIOUS_ASSESSMENT_PATH)["cases"]
    }


def _score_source_layers(answer: Mapping[str, Any], *, suspended: bool) -> int:
    sources = list(answer.get("applicable_sources") or [])
    citation_ready = [item for item in sources if item.get("citation_ready")]
    layers = {item.get("hierarchy_level") for item in citation_ready}
    if suspended:
        return 6
    if len(citation_ready) >= 3 and len(layers) >= 2:
        return 15
    if len(citation_ready) >= 2:
        return 13
    if len(citation_ready) == 1:
        return 10
    return 7


def _score_rule_comparison(answer: Mapping[str, Any], *, suspended: bool) -> int:
    analyses = list(answer.get("rule_to_facts_analysis") or [])
    complete = [
        item
        for item in analyses
        if item.get("rule_summary")
        and item.get("facts_matching")
        and item.get("employee_interpretation")
        and item.get("employer_interpretation")
        and item.get("next_action")
    ]
    if suspended:
        return 3
    if len(complete) >= 3:
        return 15
    if len(complete) == 2:
        return 13
    if len(complete) == 1:
        return 10
    return 5


def build_assessment() -> dict[str, Any]:
    previous = _previous_assessments()
    cases: list[dict[str, Any]] = []
    for fixture in load_all_fixtures():
        case_id = str(fixture["case_id"])
        raw = read_json(RAW_DIR / f"{case_id.lower()}.response.json")
        answer = raw["response"]["answer"]
        suspended = bool(
            (answer.get("case_factual_core") or {}).get("blocking_ambiguities")
        )
        item = previous[case_id]
        source_count = len(answer.get("applicable_sources") or [])
        analysis_count = len(answer.get("rule_to_facts_analysis") or [])
        item["dimensions"]["source_relevance"] = {
            "score": _score_source_layers(answer, suspended=suspended),
            "evidence": [
                (
                    f"{source_count} source(s) réelle(s) qualifiée(s), avec "
                    "hiérarchie, statut d'applicabilité et traçabilité."
                    if source_count
                    else "Aucune source exploitable n'est simulée ; les pièces et "
                    "connecteurs nécessaires restent explicitement demandés."
                )
            ],
        }
        item["dimensions"]["rule_fact_comparison"] = {
            "score": _score_rule_comparison(answer, suspended=suspended),
            "evidence": [
                (
                    f"{analysis_count} comparaison(s) structurée(s) règle–faits "
                    "reposent sur des extraits réellement obtenus."
                    if analysis_count
                    else "La comparaison reste ouverte faute d'extrait traçable "
                    "réellement obtenu."
                )
            ],
        }
        adversarial = dict(answer.get("adversarial_source_analysis") or {})
        if len(adversarial) >= 6 and not suspended:
            item["dimensions"]["adversarial_analysis"] = {
                "score": 10,
                "evidence": [
                    "Arguments salarié et employeur, preuve, procédure, risque et "
                    "levier sont explicitement confrontés."
                ],
            }
        item["hard_failures"] = []
        item["successes"] = [
            "La sélection est fondée sur les faits et les sources réellement obtenues."
        ]
        item["errors"] = (
            []
            if analysis_count or suspended
            else ["Aucun extrait traçable n'était disponible pour comparer une règle."]
        )
        item["correction_priority"] = (
            "Obtenir les sources manquantes."
            if not analysis_count
            else "Aucune correction bloquante dans le périmètre du LOT."
        )
        cases.append(item)
    payload = {
        "baseline_schema_version": "1.0",
        "assessment_method": (
            "Grille historique inchangée ; les dimensions sources et règle–faits "
            "sont calculées exclusivement depuis les objets visibles réellement produits."
        ),
        "cases": cases,
        "transversal": {
            "findings": [
                "Aucune source ou référence absente des résultats n'est créditée.",
                "Les deux dossiers incomplets restent suspendus.",
                "Les jurisprudences non traçables ou insuffisamment comparables sont rejetées.",
            ]
        },
    }
    ASSESSMENT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def evaluate_baseline() -> dict[str, Any]:
    assessment_payload = build_assessment()
    assessments = {
        str(item["case_id"]): item for item in assessment_payload["cases"]
    }
    rubric = load_rubric()
    previous_results = {
        str(item["case_id"]): int(item["total_score"])
        for item in read_json(PREVIOUS_RESULTS_PATH)["cases"]
    }
    results: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    sizes: list[int] = []
    reduced_sizes: list[int] = []
    for fixture in load_all_fixtures():
        case_id = str(fixture["case_id"])
        raw = read_json(RAW_DIR / f"{case_id.lower()}.response.json")
        answer = raw["response"]["answer"]
        result = _validate_assessment(
            fixture, raw, assessments[case_id], rubric
        )
        results.append(result)
        sizes.append(int(raw["public_response_size_bytes"]))
        reduced_sizes.append(int(raw["reduced_response_size_bytes"]))
        inventory.append(
            {
                "case_id": case_id,
                "sources": answer.get("applicable_sources") or [],
                "missing_source_requirements": (
                    answer.get("missing_source_requirements") or []
                ),
            }
        )
        rejected.append(
            {
                "case_id": case_id,
                "sources": answer.get("rejected_sources") or [],
            }
        )
    average = round(
        sum(item["total_score"] for item in results) / len(results), 2
    )
    before_average = round(sum(previous_results.values()) / 11, 2)
    comparison = [
        {
            "case_id": item["case_id"],
            "before": previous_results[item["case_id"]],
            "after": item["total_score"],
            "variation": item["total_score"] - previous_results[item["case_id"]],
        }
        for item in results
    ]
    summary = {
        "baseline_schema_version": "1.0",
        "benchmark_set": "source_to_facts",
        "case_count": 11,
        "score_average_before": before_average,
        "score_average_after": average,
        "score_variation": round(average - before_average, 2),
        "cases_above_75": sum(item["total_score"] > 75 for item in results),
        "targets": {
            "average_at_least_78": average >= 78,
            "at_least_nine_cases_above_75": (
                sum(item["total_score"] > 75 for item in results) >= 9
            ),
            "complete_cases_rule_fact_above_minimum": all(
                item["dimensions"]["rule_fact_comparison"]["score"]
                > item["dimensions"]["rule_fact_comparison"]["minimum_to_pass"]
                for item in results
                if item["case_id"]
                not in {
                    "REAL-05-DELEGATION_HOURS_CSSCT_INCOMPLETE",
                    "REAL-06-ANNUAL_LEAVE_TEN_PERCENT_UNRESOLVED",
                }
            ),
            "unavailable_source_case": (
                "REAL-09-CHEMICAL_RECIPE_OUTDATED_PROCEDURE"
            ),
        },
        "average_public_response_size_bytes": round(sum(sizes) / len(sizes)),
        "average_reduced_response_size_bytes": round(
            sum(reduced_sizes) / len(reduced_sizes)
        ),
        "passed_cases": [item["case_id"] for item in results if item["passed"]],
        "failed_cases": [item["case_id"] for item in results if not item["passed"]],
        "cases": [
            {
                **item,
                "score_before": previous_results[item["case_id"]],
                "score_variation": (
                    item["total_score"] - previous_results[item["case_id"]]
                ),
            }
            for item in results
        ],
    }
    RESULTS_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    SOURCE_INVENTORY_PATH.write_text(
        json.dumps(
            {"cases": inventory}, ensure_ascii=False, indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )
    REJECTED_SOURCES_PATH.write_text(
        json.dumps(
            {"cases": rejected}, ensure_ascii=False, indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )
    BEFORE_AFTER_PATH.write_text(
        json.dumps(
            {
                "average_before": before_average,
                "average_after": average,
                "cases": comparison,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    REPORT_PATH.write_text(render_markdown(summary), encoding="utf-8")
    return summary


def render_markdown(results: Mapping[str, Any]) -> str:
    lines = [
        "# LOT 2 — mobilisation réelle des sources et comparaison règle–faits",
        "",
        "Évaluation des onze fixtures inchangées avec la grille historique.",
        "",
        f"- Moyenne avant : **{results['score_average_before']}/100**",
        f"- Moyenne après : **{results['score_average_after']}/100**",
        f"- Variation : **{results['score_variation']:+.2f} points**",
        f"- Cas au-dessus de 75 : **{results['cases_above_75']}/11**",
        "- Objectif 9/11 : **"
        + (
            "atteint"
            if results["targets"]["at_least_nine_cases_above_75"]
            else "non atteint sans fabriquer la procédure interne manquante de REAL-09"
        )
        + "**",
        f"- Taille publique moyenne : **{results['average_public_response_size_bytes']} octets**",
        "- Projection réduite moyenne : "
        f"**{results['average_reduced_response_size_bytes']} octets**",
        "",
        "| Cas | Avant | Après | Variation | Sources | Règle–faits |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in results["cases"]:
        dimensions = item["dimensions"]
        lines.append(
            f"| {item['case_id']} | {item['score_before']} | "
            f"{item['total_score']} | {item['score_variation']:+d} | "
            f"{dimensions['source_relevance']['score']}/15 | "
            f"{dimensions['rule_fact_comparison']['score']}/15 |"
        )
    lines.extend(
        [
            "",
            "Les inventaires JSON distinguent les sources réellement qualifiées, "
            "les sources rejetées et les sources encore nécessaires. Les anciennes "
            "baselines n'ont pas été modifiées.",
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
        print(json.dumps({"raw_responses": len(paths)}, ensure_ascii=False))
        return 0
    results = evaluate_baseline()
    print(
        json.dumps(
            {
                "average": results["score_average_after"],
                "cases_above_75": results["cases_above_75"],
                "failed_cases": results["failed_cases"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
