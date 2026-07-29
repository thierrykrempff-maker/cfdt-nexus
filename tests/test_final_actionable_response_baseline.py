from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = (
    ROOT
    / "tests"
    / "fixtures"
    / "real_business_cases"
    / "final_response_baseline"
)


def load(name: str):
    return json.loads((BASELINE / name).read_text(encoding="utf-8"))


def test_baseline_covers_the_unchanged_eleven_cases() -> None:
    results = load("final-response-results.json")
    raw = sorted((BASELINE / "raw").glob("*.response.json"))

    assert results["case_count"] == 11
    assert len(raw) == 11
    assert results["score_average_lot3"] == results["score_average_lot2"] == 85.36
    assert results["cases_above_75"] >= 8


def test_all_sizes_and_section_counts_respect_hard_limits() -> None:
    sizes = load("response-sizes.json")
    sections = load("section-inventory.json")

    assert sizes["average_bytes"] < 30_000
    assert all(item["within_hard_limit"] for item in sizes["cases"])
    assert all(item["within_limit"] for item in sections["cases"])


def test_suspended_cases_remain_suspended_and_short() -> None:
    results = load("final-response-results.json")
    suspended = [item for item in results["cases"] if item["analysis_suspended"]]

    assert len(suspended) == 2
    assert all(item["public_response_size_bytes"] < 25_000 for item in suspended)


def test_exports_exclude_details_and_summaries_have_no_exact_duplicates() -> None:
    export = load("export-validation.json")
    duplicates = load("deduplication-report.json")

    assert export["all_cases_valid"] is True
    assert export["details_excluded"] is True
    assert duplicates["all_cases_without_duplicate"] is True
