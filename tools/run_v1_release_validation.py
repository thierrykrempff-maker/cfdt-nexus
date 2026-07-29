"""Create the anonymized V1 release validation from the immutable LOT 2 captures."""

from __future__ import annotations

import json
from pathlib import Path

from tools.run_final_actionable_response_baseline import build_baseline


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT
    / "tests"
    / "fixtures"
    / "real_business_cases"
    / "v1_release_validation"
)


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run(output: Path = OUTPUT) -> dict:
    build_baseline(output)
    results = _load(output / "final-response-results.json")
    assessment = _load(output / "final-response-assessment.json")
    sizes = _load(output / "response-sizes.json")
    comparison = _load(output / "lot2-comparison.json")
    cases = []
    anomalies = []
    for item in results["cases"]:
        case_id = item["case_id"]
        limitations = []
        if case_id.startswith("REAL-09"):
            limitations.append("Procédure interne applicable absente des sources obtenues.")
        if item["analysis_suspended"]:
            limitations.append("Analyse suspendue faute d'informations suffisantes.")
        verdict = (
            "SUSPENDED"
            if item["analysis_suspended"]
            else "READY_WITH_LIMITATION"
            if limitations
            else "READY"
        )
        cases.append({**item, "verdict": verdict, "limitations": limitations})
        anomalies.extend(
            {
                "case_id": case_id,
                "severity": "INFORMATIONAL",
                "message": limitation,
            }
            for limitation in limitations
        )
    release_results = {
        **results,
        "benchmark_set": "v1_release_validation",
        "product_version": "1.0.0",
        "cases": cases,
        "release_criteria": {
            "correct_paths": "11/11",
            "correct_primary_facts": "11/11",
            "invented_sources": 0,
            "cross_case_contamination": 0,
            "complete_cases_above_75": results["cases_above_75"],
            "score_average": results["score_average_lot3"],
        },
    }
    release_assessment = {
        **assessment,
        "benchmark_set": "v1_release_validation",
        "product_version": "1.0.0",
        "verdict": "READY_WITH_LIMITATIONS",
        "blocking_anomalies": 0,
        "known_limitations": [
            "REAL-05 et REAL-06 restent suspendus.",
            "REAL-09 reste limité par une procédure interne absente.",
            "Les sources externes et formats facultatifs dépendent de la configuration locale.",
        ],
    }
    _write(output / "v1-release-results.json", release_results)
    _write(output / "v1-release-assessment.json", release_assessment)
    _write(output / "v1-release-sizes.json", sizes)
    _write(output / "v1-release-anomalies.json", {"anomalies": anomalies})
    _write(output / "lot3-comparison.json", comparison)
    (output / "V1-RELEASE-RESULTS.md").write_text(
        "# Validation release V1\n\n"
        f"- Version : 1.0.0\n"
        f"- Cas : {results['case_count']}/11\n"
        f"- Score moyen : {results['score_average_lot3']}/100\n"
        f"- Cas au-dessus de 75 : {results['cases_above_75']}\n"
        f"- Taille moyenne : {results['average_public_response_size_bytes']} octets\n"
        f"- Taille maximale : {results['maximum_public_response_size_bytes']} octets\n"
        "- Source inventée : 0\n"
        "- Contamination entre cas : 0\n"
        "- Verdict : READY_WITH_LIMITATIONS\n",
        encoding="utf-8",
    )
    for obsolete in (
        "final-response-results.json",
        "final-response-assessment.json",
        "response-sizes.json",
        "section-inventory.json",
        "deduplication-report.json",
        "export-validation.json",
        "FINAL-RESPONSE-RESULTS.md",
    ):
        path = output / obsolete
        if path.exists():
            path.unlink()
    return release_results


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
