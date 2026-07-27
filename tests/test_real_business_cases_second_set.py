from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import jsonschema

from tools.run_real_business_cases_baseline import (
    DIMENSION_ORDER,
    build_case_prompt,
    sha256,
)
from tools.run_real_business_cases_second_baseline import (
    EXPECTED_CASES,
    RAW_DIR,
    RESULTS_PATH,
    load_second_fixtures,
)


ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "tests" / "fixtures" / "real_business_cases"
SECOND_DIR = CORPUS_DIR / "second_set"


def test_five_second_set_fixtures_are_schema_compliant_and_anonymized() -> None:
    schema = json.loads((CORPUS_DIR / "fixture.schema.json").read_text(encoding="utf-8"))
    fixtures = load_second_fixtures()

    assert len(fixtures) == 5
    assert {item["case_id"] for item in fixtures} == EXPECTED_CASES
    for fixture in fixtures:
        candidate = {key: value for key, value in fixture.items() if key != "_fixture_path"}
        jsonschema.Draft202012Validator(schema).validate(candidate)
        assert fixture["privacy"]["anonymized"] is True
        assert fixture["privacy"]["direct_identifiers"] == []
        assert fixture["case_input"]["requested_path"] in {
            "QUESTION_SALARIE",
            "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE",
        }


def test_second_set_prompt_exposes_only_case_input() -> None:
    for fixture in load_second_fixtures():
        protected = deepcopy(fixture)
        protected["evaluation_expectations"] = {"sentinel": "EXPECTATIONS_MUST_NOT_LEAK"}
        protected["evaluation_only"]["known_outcome"]["facts"] = [
            "KNOWN_OUTCOME_MUST_NOT_LEAK"
        ]

        prompt = build_case_prompt(protected)

        assert "EXPECTATIONS_MUST_NOT_LEAK" not in prompt
        assert "KNOWN_OUTCOME_MUST_NOT_LEAK" not in prompt
        assert protected["case_input"]["requested_path"] not in prompt


def test_known_outcomes_are_absent_from_case_input() -> None:
    for fixture in load_second_fixtures():
        case_input = json.dumps(fixture["case_input"], ensure_ascii=False).casefold()
        for outcome in fixture["evaluation_only"]["known_outcome"]["facts"]:
            assert outcome.casefold() not in case_input
    ppe = next(
        item
        for item in load_second_fixtures()
        if item["case_id"] == "REAL-07-SAFETY_PPE_UNAVAILABLE_OR_UNSUITABLE"
    )
    assert "trois jours" not in json.dumps(ppe["case_input"], ensure_ascii=False)


def test_legal_reference_register_uses_only_explicit_statuses() -> None:
    register = json.loads(
        (SECOND_DIR / "legal-references-to-verify.json").read_text(encoding="utf-8")
    )
    allowed = {
        "VERIFIED",
        "TO_VERIFY",
        "INCOMPLETE_REFERENCE",
        "UNSUPPORTED_ASSERTION",
    }
    assert set(register["allowed_statuses"]) == allowed
    assert register["references"]
    assert all(item["status"] in allowed for item in register["references"])
    assert not any(item["status"] == "VERIFIED" for item in register["references"])


def test_second_raw_responses_are_isolated_and_reproducible() -> None:
    fixtures = load_second_fixtures()
    raw_files = sorted(RAW_DIR.glob("*.response.json"))

    assert len(raw_files) == 5
    raw_by_id = {
        payload["case_id"]: payload
        for payload in (
            json.loads(path.read_text(encoding="utf-8")) for path in raw_files
        )
    }
    assert set(raw_by_id) == EXPECTED_CASES
    for fixture in fixtures:
        raw = raw_by_id[fixture["case_id"]]
        prompt = build_case_prompt(fixture)
        assert raw["case_input_sha256"] == sha256(fixture["case_input"])
        assert raw["prompt_sha256"] == hashlib.sha256(
            prompt.encode("utf-8")
        ).hexdigest()
        assert raw["evaluation_data_exposed_to_nexus"] is False
        assert raw["employee_path"] == fixture["case_input"]["requested_path"]
        assert raw["response"]["ok"] is True
        assert raw["response"]["answer"]["route"]["query"] == prompt
    assert sum(path.stat().st_size for path in raw_files) < 1_000_000


def test_second_baseline_results_apply_existing_rubric() -> None:
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))

    assert results["case_count"] == 5
    assert results["initial_baseline_average"] == 32.67
    for case in results["cases"]:
        assert set(case["dimensions"]) == set(DIMENSION_ORDER)
        assert sum(
            item["score"] for item in case["dimensions"].values()
        ) == case["total_score"]
        if case["dimensions"]["factual_understanding"]["score"] < 14:
            assert "FACTUAL_MISUNDERSTANDING" in case["hard_failures"]


def test_second_set_has_no_direct_identifier_or_secret_marker() -> None:
    rendered = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(SECOND_DIR.rglob("*.json"))
    ).casefold()
    for marker in (
        "@gmail.",
        "@outlook.",
        "c:\\users\\",
        "matricule:",
        "numéro de sécurité sociale:",
        "iban:",
        "client_secret",
        "access_token",
        "refresh_token",
    ):
        assert marker not in rendered
