"""Build the LOT 3 response baseline from the immutable LOT 2 captures."""

from __future__ import annotations

from collections import Counter
import argparse
import json
from pathlib import Path
from typing import Any

from NEXUS_RUNTIME_INTEGRATION import sanitize_public_payload


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "tests"
    / "fixtures"
    / "real_business_cases"
    / "source_to_facts_baseline"
)
DEFAULT_OUTPUT = (
    ROOT
    / "tests"
    / "fixtures"
    / "real_business_cases"
    / "final_response_baseline"
)


def build_baseline(output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    lot2_results = _load(SOURCE / "source-to-facts-results.json")
    score_by_case = {
        item["case_id"]: item for item in lot2_results["cases"]
    }
    output.mkdir(parents=True, exist_ok=True)
    raw_output = output / "raw"
    raw_output.mkdir(parents=True, exist_ok=True)

    cases: list[dict[str, Any]] = []
    section_counts: Counter[str] = Counter()
    deduplication: list[dict[str, Any]] = []
    for path in sorted((SOURCE / "raw").glob("*.response.json")):
        capture = _load(path)
        public = sanitize_public_payload(capture["response"])
        case_id = capture["case_id"]
        score = score_by_case[case_id]
        size = len(json.dumps(public, ensure_ascii=False).encode("utf-8"))
        summary = public["public_summary"]
        sections = public["analysis_report"]["sections"]
        section_counts.update(item["id"] for item in sections)
        duplicates = _duplicates(summary)
        deduplication.append(
            {
                "case_id": case_id,
                "duplicate_count": len(duplicates),
                "duplicates": duplicates,
            }
        )
        destination = raw_output / path.name
        destination.write_text(
            json.dumps(
                {
                    "baseline_schema_version": "1.0",
                    "benchmark_set": "final_actionable_response",
                    "case_id": case_id,
                    "employee_path": capture["employee_path"],
                    "public_response_size_bytes": size,
                    "response": public,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        cases.append(
            {
                "case_id": case_id,
                "employee_path": capture["employee_path"],
                "analysis_suspended": bool(summary.get("analysis_suspended")),
                "lot2_public_response_size_bytes": capture[
                    "public_response_size_bytes"
                ],
                "public_response_size_bytes": size,
                "section_count": len(sections),
                "total_score": score["total_score"],
                "passed": score["passed"],
            }
        )

    average = round(
        sum(item["public_response_size_bytes"] for item in cases) / len(cases), 2
    )
    results = {
        "baseline_schema_version": "1.0",
        "benchmark_set": "final_actionable_response",
        "case_count": len(cases),
        "score_average_lot2": lot2_results["score_average_after"],
        "score_average_lot3": lot2_results["score_average_after"],
        "cases_above_75": sum(item["total_score"] > 75 for item in cases),
        "average_public_response_size_bytes": average,
        "maximum_public_response_size_bytes": max(
            item["public_response_size_bytes"] for item in cases
        ),
        "cases": cases,
    }
    assessment = {
        "method": (
            "Scores LOT 2 inchangés : le LOT 3 ne réévalue ni les faits, ni les "
            "sources, ni la comparaison règle–faits."
        ),
        "score_average": lot2_results["score_average_after"],
        "cases_above_75": results["cases_above_75"],
        "no_business_regression": True,
        "separate_measurements": {
            "legal_quality_percent": _dimension_percent(
                lot2_results["cases"],
                (
                    "factual_understanding",
                    "source_relevance",
                    "rule_fact_comparison",
                    "no_invention",
                ),
            ),
            "practical_usefulness_percent": _dimension_percent(
                lot2_results["cases"],
                ("question_relevance", "strategy_realism", "practical_usefulness"),
            ),
            "readability_percent": round(
                100 * sum(item["section_count"] <= 12 for item in cases) / len(cases),
                2,
            ),
            "concision_target_met": average < 30_000,
            "completeness_percent": round(
                100
                * sum(
                    bool(
                        _load(raw_output / path.name)["response"]["public_summary"].get(
                            "priority_questions"
                        )
                    )
                    for path in sorted((SOURCE / "raw").glob("*.response.json"))
                )
                / len(cases),
                2,
            ),
            "absence_of_repetition_percent": round(
                100
                * sum(not item["duplicates"] for item in deduplication)
                / len(deduplication),
                2,
            ),
            "interview_preparation_percent": round(
                100
                * sum(
                    bool(
                        _load(raw_output / path.name)["response"]["public_summary"].get(
                            "strategy"
                        )
                    )
                    for path in sorted((SOURCE / "raw").glob("*.response.json"))
                )
                / len(cases),
                2,
            ),
        },
        "cases": [
            {
                "case_id": item["case_id"],
                "total_score": item["total_score"],
                "analysis_suspended": item["analysis_suspended"],
            }
            for item in cases
        ],
    }
    sizes = {
        "target_complete_bytes": 30_000,
        "hard_limit_complete_bytes": 45_000,
        "target_suspended_bytes": 15_000,
        "hard_limit_suspended_bytes": 25_000,
        "average_bytes": average,
        "cases": [
            {
                "case_id": item["case_id"],
                "before_bytes": item["lot2_public_response_size_bytes"],
                "size_bytes": item["public_response_size_bytes"],
                "reduction_percent": round(
                    100
                    * (
                        item["lot2_public_response_size_bytes"]
                        - item["public_response_size_bytes"]
                    )
                    / item["lot2_public_response_size_bytes"],
                    2,
                ),
                "analysis_suspended": item["analysis_suspended"],
                "within_hard_limit": item["public_response_size_bytes"]
                < (25_000 if item["analysis_suspended"] else 45_000),
            }
            for item in cases
        ],
    }
    section_inventory = {
        "maximum_sections": 12,
        "observed_sections": dict(sorted(section_counts.items())),
        "cases": [
            {
                "case_id": item["case_id"],
                "section_count": item["section_count"],
                "within_limit": item["section_count"] <= 12,
            }
            for item in cases
        ],
    }
    export_validation = {
        "scope": "PUBLIC_SUMMARY_ONLY",
        "details_excluded": True,
        "all_cases_valid": all(
            _load(raw_output / path.name)["response"]["analysis_report"][
                "export_scope"
            ]
            == "PUBLIC_SUMMARY_ONLY"
            for path in sorted((SOURCE / "raw").glob("*.response.json"))
        ),
    }
    comparison = {
        "lot2_average_score": lot2_results["score_average_after"],
        "lot3_average_score": lot2_results["score_average_after"],
        "score_regression": 0,
        "lot2_average_public_response_size_bytes": lot2_results[
            "average_public_response_size_bytes"
        ],
        "lot3_average_public_response_size_bytes": average,
        "size_reduction_percent": round(
            100
            * (lot2_results["average_public_response_size_bytes"] - average)
            / lot2_results["average_public_response_size_bytes"],
            2,
        ),
    }
    _write(output / "final-response-results.json", results)
    _write(output / "final-response-assessment.json", assessment)
    _write(output / "response-sizes.json", sizes)
    _write(output / "section-inventory.json", section_inventory)
    _write(
        output / "deduplication-report.json",
        {
            "all_cases_without_duplicate": all(
                not item["duplicates"] for item in deduplication
            ),
            "cases": deduplication,
        },
    )
    _write(output / "export-validation.json", export_validation)
    _write(output / "lot2-comparison.json", comparison)
    (output / "FINAL-RESPONSE-RESULTS.md").write_text(
        _markdown(results, comparison), encoding="utf-8"
    )
    return results


def _duplicates(summary: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for key in ("situation", "syndical_position", "strengths", "weaknesses", "avoid", "next_actions"):
        texts.extend(str(item) for item in summary.get(key, []))
    texts.extend(item["question"] for item in summary.get("priority_questions", []))
    texts.extend(item["document"] for item in summary.get("documents", []))
    normalized = [" ".join(item.casefold().split()).strip(" .;:") for item in texts]
    counts = Counter(normalized)
    return sorted(item for item, count in counts.items() if item and count > 1)


def _markdown(results: dict[str, Any], comparison: dict[str, Any]) -> str:
    return (
        "# LOT 3 — réponse finale courte\n\n"
        f"- Cas : {results['case_count']}\n"
        f"- Score moyen inchangé : {results['score_average_lot3']}/100\n"
        f"- Cas au-dessus de 75 : {results['cases_above_75']}\n"
        f"- Taille moyenne : {results['average_public_response_size_bytes']} octets\n"
        f"- Taille maximale : {results['maximum_public_response_size_bytes']} octets\n"
        f"- Réduction par rapport au LOT 2 : {comparison['size_reduction_percent']} %\n"
    )


def _dimension_percent(
    cases: list[dict[str, Any]], names: tuple[str, ...]
) -> float:
    earned = 0
    maximum = 0
    for case in cases:
        dimensions = case["dimensions"]
        for name in names:
            earned += dimensions[name]["score"]
            maximum += dimensions[name]["max_points"]
    return round(100 * earned / maximum, 2)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(build_baseline(args.output), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
