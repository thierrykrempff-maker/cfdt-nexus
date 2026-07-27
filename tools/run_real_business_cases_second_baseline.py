#!/usr/bin/env python
"""Run and evaluate the second anonymized real-business-case Nexus baseline.

Only ``case_input`` is converted to a prompt. Evaluation expectations and
known outcomes are never passed to Nexus.
"""

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
    _load_server_module,
    _validate_assessment,
    build_case_prompt,
    load_rubric,
    reduce_public_response,
    sha256,
)


ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "tests" / "fixtures" / "real_business_cases"
SECOND_DIR = CORPUS_DIR / "second_set"
RAW_DIR = SECOND_DIR / "baseline" / "raw"
ASSESSMENT_PATH = SECOND_DIR / "baseline" / "second-baseline-assessment.json"
RESULTS_PATH = SECOND_DIR / "baseline" / "second-baseline-results.json"
REPORT_PATH = SECOND_DIR / "baseline" / "SECOND-BASELINE.md"

EXPECTED_CASES = {
    "REAL-07-SAFETY_PPE_UNAVAILABLE_OR_UNSUITABLE",
    "REAL-08-TEMPORARY_DAY_TO_THREE_SHIFT_REFUSAL",
    "REAL-09-CHEMICAL_RECIPE_OUTDATED_PROCEDURE",
    "REAL-10-POSITIVE_ALCOHOL_TEST_HIGH_RISK_POSITION",
    "REAL-11-INSULTS_SUPERVISOR_FATIGUE_CONTEXT",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_second_fixtures() -> tuple[dict[str, Any], ...]:
    fixtures: list[dict[str, Any]] = []
    for path in sorted(SECOND_DIR.glob("*.json")):
        payload = read_json(path)
        if "case_id" not in payload:
            continue
        payload["_fixture_path"] = str(path.relative_to(ROOT)).replace("\\", "/")
        fixtures.append(payload)
    identifiers = [str(item["case_id"]) for item in fixtures]
    if set(identifiers) != EXPECTED_CASES or len(identifiers) != len(EXPECTED_CASES):
        raise ValueError(f"Expected exactly five second-set cases, got {identifiers!r}.")
    return tuple(sorted(fixtures, key=lambda item: str(item["case_id"])))


def run_second_baseline(*, source_limit: int = 8) -> tuple[Path, ...]:
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = os.pathsep.join(
        item for item in (str(ROOT), existing_pythonpath) if item
    )
    server = _load_server_module()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for fixture in load_second_fixtures():
        case_input = deepcopy(fixture["case_input"])
        prompt = build_case_prompt({"case_input": case_input})
        employee_path = str(case_input["requested_path"])
        response = server.analyze_public_question(prompt, source_limit, employee_path)
        envelope = {
            "baseline_schema_version": "1.0",
            "benchmark_set": "second_set",
            "case_id": fixture["case_id"],
            "fixture_path": fixture["_fixture_path"],
            "employee_path": employee_path,
            "case_input_sha256": sha256(case_input),
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "evaluation_data_exposed_to_nexus": False,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "response_projection": "visible_baseline_v1",
            "response": reduce_public_response(response),
        }
        output = RAW_DIR / f"{str(fixture['case_id']).lower()}.response.json"
        output.write_text(
            json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        created.append(output)
    return tuple(created)


def evaluate_second_baseline() -> dict[str, Any]:
    rubric = load_rubric()
    assessment_payload = read_json(ASSESSMENT_PATH)
    assessments = {
        str(item["case_id"]): item for item in assessment_payload.get("cases", ())
    }
    results: list[dict[str, Any]] = []
    for fixture in load_second_fixtures():
        case_id = str(fixture["case_id"])
        raw_path = RAW_DIR / f"{case_id.lower()}.response.json"
        if not raw_path.exists() or case_id not in assessments:
            raise ValueError(f"Missing raw response or assessment for {case_id}.")
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
        "benchmark_set": "second_set",
        "case_count": len(results),
        "score_average": round(
            sum(item["total_score"] for item in results) / len(results), 2
        ),
        "initial_baseline_average": 32.67,
        "difference_from_initial_baseline": round(
            sum(item["total_score"] for item in results) / len(results) - 32.67, 2
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
    lines = [
        "# Seconde baseline Nexus — cas métier réels anonymisés",
        "",
        "Cette mesure utilise le moteur Nexus existant, sans modification de moteur, "
        "routeur, connecteur, runtime ou interface.",
        "",
        f"- Cas exécutés : {results['case_count']}",
        f"- Score moyen du second lot : **{results['score_average']}/100**",
        f"- Baseline initiale : **{results['initial_baseline_average']}/100**",
        f"- Écart : **{results['difference_from_initial_baseline']:+.2f} points**",
        f"- Cas réussis : {len(results['passed_cases'])}",
        f"- Cas en échec : {len(results['failed_cases'])}",
        "",
        "## Limites",
        "",
        "- Les réponses mesurent la configuration locale disponible lors de l'exécution.",
        "- Les sources locales ou officielles indisponibles sont une limite de mesure.",
        "- Les références non vérifiables du récit source sont isolées dans "
        "`legal-references-to-verify.json` et ne servent pas d'autorité.",
        "- Ni `evaluation_expectations` ni `evaluation_only` n'ont été transmis à Nexus.",
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
                f"- Priorité : {result['correction_priority']}",
                "",
                "### Réussites",
                "",
            ]
        )
        lines.extend(f"- {item}" for item in result["successes"] or ["Aucune."])
        lines.extend(["", "### Erreurs", ""])
        lines.extend(f"- {item}" for item in result["errors"] or ["Aucune."])
        lines.extend(["", "### Questions essentielles absentes", ""])
        lines.extend(
            f"- {item}"
            for item in result["missing_essential_questions"] or ["Aucune."]
        )
    lines.extend(["", "## Synthèse transversale", ""])
    for item in results.get("transversal", {}).get("findings", ()):
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "evaluate"))
    parser.add_argument("--source-limit", type=int, default=8)
    args = parser.parse_args()
    if args.command == "run":
        paths = run_second_baseline(source_limit=args.source_limit)
        print(
            json.dumps(
                {"raw_responses": [str(path.relative_to(ROOT)) for path in paths]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    results = evaluate_second_baseline()
    print(
        json.dumps(
            {
                "case_count": results["case_count"],
                "score_average": results["score_average"],
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
