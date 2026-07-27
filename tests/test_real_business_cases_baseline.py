from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from tools.run_real_business_cases_baseline import (
    DIMENSION_ORDER,
    RAW_DIR,
    ROUTE_BY_CASE,
    RESULTS_PATH,
    build_case_prompt,
    load_fixtures,
    load_rubric,
    sha256,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "real_business_cases"


def test_six_anonymized_fixtures_are_present() -> None:
    fixtures = load_fixtures()

    assert len(fixtures) == 6
    assert {item["case_id"] for item in fixtures} == set(ROUTE_BY_CASE)
    assert all(item["privacy"]["anonymized"] is True for item in fixtures)
    assert all(item["privacy"]["direct_identifiers"] == [] for item in fixtures)


def test_every_fixture_has_separated_fact_states_and_evaluator_data() -> None:
    for fixture in load_fixtures():
        assert set(fixture["case_input"]) == {
            "facts_provided",
            "facts_recognized",
            "facts_contested",
            "facts_alleged",
            "missing_information",
        }
        assert fixture["evaluation_expectations"]
        assert fixture["evaluation_only"]["never_include_in_initial_prompt"] is True
        assert fixture["evaluation_only"]["known_outcome"]["evaluation_use_only"] == (
            "realism_check_after_response"
        )


def test_prompt_builder_cannot_expose_evaluator_expectations_or_known_outcome() -> None:
    for fixture in load_fixtures():
        protected = deepcopy(fixture)
        protected["evaluation_expectations"] = {
            "sentinel": "EVALUATOR_EXPECTATIONS_MUST_NOT_LEAK"
        }
        protected["evaluation_only"]["known_outcome"]["facts"] = [
            "KNOWN_OUTCOME_MUST_NOT_LEAK"
        ]

        prompt = build_case_prompt(protected)

        assert "EVALUATOR_EXPECTATIONS_MUST_NOT_LEAK" not in prompt
        assert "KNOWN_OUTCOME_MUST_NOT_LEAK" not in prompt
        for fact in fixture["case_input"]["facts_provided"]:
            assert fact in prompt


def test_cssct_case_is_explicitly_incomplete() -> None:
    fixture = next(
        item
        for item in load_fixtures()
        if item["case_id"] == "REAL-05-DELEGATION_HOURS_CSSCT_INCOMPLETE"
    )

    assert fixture["completeness"]["status"] == "incomplete"
    assert fixture["completeness"]["analysis_state"] == (
        "unresolved_pending_clarification"
    )
    rendered = json.dumps(fixture, ensure_ascii=False).casefold()
    assert "fin manquante du récit" in rendered


def test_ten_percent_case_stays_unresolved_and_requires_definition_first() -> None:
    fixture = next(
        item
        for item in load_fixtures()
        if item["case_id"] == "REAL-06-ANNUAL_LEAVE_TEN_PERCENT_UNRESOLVED"
    )

    assert fixture["completeness"]["analysis_state"] == (
        "unresolved_pending_clarification"
    )
    assert fixture["evaluation_expectations"]["priority_questions"][0][
        "question"
    ].startswith("Que signifie exactement")
    rendered = json.dumps(fixture["evaluation_expectations"], ensure_ascii=False)
    assert "Supposer directement qu'il s'agit de la règle légale du dixième" in rendered


def test_rubric_has_eight_dimensions_totalling_one_hundred() -> None:
    rubric = load_rubric()

    assert tuple(item["id"] for item in rubric["dimensions"]) == DIMENSION_ORDER
    assert sum(item["max_points"] for item in rubric["dimensions"]) == 100
    assert rubric["known_outcome_protocol"]["visible_during_response_generation"] is False
    assert rubric["known_outcome_protocol"]["may_add_points"] is False


def test_no_direct_identifier_marker_is_present() -> None:
    rendered = json.dumps(load_fixtures(), ensure_ascii=False).casefold()

    for marker in (
        "@gmail.",
        "@outlook.",
        "c:\\users\\",
        "matricule:",
        "adresse électronique:",
        "numéro de sécurité sociale:",
        "iban:",
    ):
        assert marker not in rendered


def test_raw_baseline_contains_six_isolated_public_responses() -> None:
    fixtures = load_fixtures()
    raw_files = sorted(RAW_DIR.glob("*.response.json"))

    assert len(raw_files) == 6
    raw_by_id = {
        payload["case_id"]: payload
        for payload in (
            json.loads(path.read_text(encoding="utf-8")) for path in raw_files
        )
    }
    assert set(raw_by_id) == set(ROUTE_BY_CASE)
    for fixture in fixtures:
        raw = raw_by_id[fixture["case_id"]]
        prompt = build_case_prompt(fixture)
        assert raw["case_input_sha256"] == sha256(fixture["case_input"])
        assert raw["prompt_sha256"] == hashlib.sha256(
            prompt.encode("utf-8")
        ).hexdigest()
        assert raw["evaluation_data_exposed_to_nexus"] is False
        assert raw["response_projection"] == "visible_baseline_v1"
        assert raw["employee_path"] == ROUTE_BY_CASE[fixture["case_id"]]
        assert raw["response"]["ok"] is True
        assert raw["response"]["answer"]["route"]["query"] == prompt
        assert "experts" not in raw["response"]
        assert "runtime_integration" not in raw["response"]
        assert "markdown" not in raw["response"]["analysis_report"]

    assert sum(path.stat().st_size for path in raw_files) < 1_000_000


def test_baseline_results_are_complete_and_apply_factual_gate() -> None:
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))

    assert results["case_count"] == 6
    assert results["score_average"] == 32.67
    assert results["passed_cases"] == []
    assert len(results["failed_cases"]) == 6
    for case in results["cases"]:
        assert set(case["dimensions"]) == set(DIMENSION_ORDER)
        assert sum(
            item["score"] for item in case["dimensions"].values()
        ) == case["total_score"]
        assert "FACTUAL_MISUNDERSTANDING" in case["hard_failures"]
        assert case["known_outcome_used_only_after_core_scoring"] is True
