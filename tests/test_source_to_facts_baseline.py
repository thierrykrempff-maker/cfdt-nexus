from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
BASELINE = (
    ROOT
    / "tests"
    / "fixtures"
    / "real_business_cases"
    / "source_to_facts_baseline"
)
EXPECTED_CASES = {
    "REAL-01-INSULTING_EMAILS_ALCOHOL",
    "REAL-02-SMOKING_BREAKS_SEVESO_BADGE",
    "REAL-03-TAG_INSTALLATION",
    "REAL-04-FORCED_DAY_TO_SHIFT_LABORATORY",
    "REAL-05-DELEGATION_HOURS_CSSCT_INCOMPLETE",
    "REAL-06-ANNUAL_LEAVE_TEN_PERCENT_UNRESOLVED",
    "REAL-07-SAFETY_PPE_UNAVAILABLE_OR_UNSUITABLE",
    "REAL-08-TEMPORARY_DAY_TO_THREE_SHIFT_REFUSAL",
    "REAL-09-CHEMICAL_RECIPE_OUTDATED_PROCEDURE",
    "REAL-10-POSITIVE_ALCOHOL_TEST_HIGH_RISK_POSITION",
    "REAL-11-INSULTS_SUPERVISOR_FATIGUE_CONTEXT",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_baseline_contains_eleven_unchanged_reference_cases() -> None:
    raw_files = tuple(sorted((BASELINE / "raw").glob("*.response.json")))
    payloads = [read_json(path) for path in raw_files]

    assert len(raw_files) == 11
    assert {item["case_id"] for item in payloads} == EXPECTED_CASES
    assert all(item["evaluation_data_exposed_to_nexus"] is False for item in payloads)
    assert all(item["case_input_sha256"] for item in payloads)
    assert all(item["prompt_sha256"] for item in payloads)


def test_measured_baseline_exceeds_average_target_without_faking_sources() -> None:
    results = read_json(BASELINE / "source-to-facts-results.json")

    assert results["case_count"] == 11
    assert results["score_average_after"] >= 78
    assert results["score_average_after"] > results["score_average_before"]
    assert results["cases_above_75"] >= 8
    assert set(results["failed_cases"]) == {
        "REAL-05-DELEGATION_HOURS_CSSCT_INCOMPLETE",
        "REAL-06-ANNUAL_LEAVE_TEN_PERCENT_UNRESOLVED",
        "REAL-09-CHEMICAL_RECIPE_OUTDATED_PROCEDURE",
    }


def test_incomplete_cases_remain_suspended_and_source_free() -> None:
    for case_prefix in ("real-05-", "real-06-"):
        path = next((BASELINE / "raw").glob(f"{case_prefix}*.response.json"))
        answer = read_json(path)["response"]["answer"]

        assert answer["case_factual_core"]["blocking_ambiguities"]
        assert answer["applicable_sources"] == []
        assert answer["rule_to_facts_analysis"] == []
        assert answer["missing_source_requirements"]


def test_every_retained_case_law_is_traceable_and_factually_comparable() -> None:
    inventory = read_json(BASELINE / "source-inventory.json")
    decisions = [
        source
        for case in inventory["cases"]
        for source in case["sources"]
        if source["legal_nature"] == "CASE_LAW"
    ]

    assert all(source["factual_similarity_score"] >= 39 for source in decisions)
    assert all(source["source_location"] for source in decisions)
    assert all(source["citation_ready"] for source in decisions)


def test_reduced_responses_do_not_expose_local_paths_or_sensitive_values() -> None:
    prohibited = re.compile(
        r"(?:[A-Z]:\\|/(?:tmp|home|Users)/|"
        r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\bFR\d{2}[A-Z0-9]{23}\b)",
        re.IGNORECASE,
    )
    for path in (BASELINE / "raw").glob("*.response.json"):
        text = path.read_text(encoding="utf-8")
        assert prohibited.search(text) is None


def test_inventory_separates_obtained_rejected_and_missing_sources() -> None:
    inventory = read_json(BASELINE / "source-inventory.json")
    rejected = read_json(BASELINE / "rejected-sources.json")

    assert {item["case_id"] for item in inventory["cases"]} == EXPECTED_CASES
    assert {item["case_id"] for item in rejected["cases"]} == EXPECTED_CASES
    assert any(item["sources"] for item in inventory["cases"])
    assert any(item["sources"] for item in rejected["cases"])
    assert all(
        "reason" in source
        for item in rejected["cases"]
        for source in item["sources"]
    )
