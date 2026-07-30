from __future__ import annotations

import json
from pathlib import Path

from SYNDICAL_REASONING_ENGINE import build_case_factual_core
from tools.run_real_business_cases_baseline import (
    ROUTE_BY_CASE,
    build_case_prompt,
    load_fixtures,
)
from tools.run_real_business_cases_second_baseline import load_second_fixtures


ROOT = Path(__file__).resolve().parents[1]


def test_fact_and_session_ids_are_stable_for_the_same_analysis() -> None:
    query = """
Faits reconnus :
- Le salarié reconnaît certains mots.
Faits contestés :
- Le salarié conteste la diffusion.
"""
    first = build_case_factual_core(query, "QUESTION_SALARIE")
    second = build_case_factual_core(query, "QUESTION_SALARIE")

    assert first.origin_session_id == second.origin_session_id
    assert [fact.fact_id for fact in first.canonical_facts] == [
        fact.fact_id for fact in second.canonical_facts
    ]
    assert first.to_dict() == second.to_dict()


def test_explicit_case_sessions_isolate_identical_wording() -> None:
    query = "Faits allégués :\n- Une fatigue importante est alléguée."
    first = build_case_factual_core(query, origin_session_id="session-one")
    second = build_case_factual_core(query, origin_session_id="session-two")

    assert first.canonical_facts[0].fact_id != second.canonical_facts[0].fact_id


def test_eleven_historical_statuses_scores_and_fixtures_remain_unchanged() -> None:
    fixtures = (*load_fixtures(), *load_second_fixtures())
    assessment_path = (
        ROOT
        / "tests"
        / "fixtures"
        / "real_business_cases"
        / "v1_release_validation"
        / "v1-release-assessment.json"
    )
    assessment = json.loads(assessment_path.read_text(encoding="utf-8"))
    scores = {item["case_id"]: item["total_score"] for item in assessment["cases"]}

    assert len(fixtures) == 11
    assert scores == {
        "REAL-01-INSULTING_EMAILS_ALCOHOL": 92,
        "REAL-02-SMOKING_BREAKS_SEVESO_BADGE": 93,
        "REAL-03-TAG_INSTALLATION": 92,
        "REAL-04-FORCED_DAY_TO_SHIFT_LABORATORY": 92,
        "REAL-05-DELEGATION_HOURS_CSSCT_INCOMPLETE": 70,
        "REAL-06-ANNUAL_LEAVE_TEN_PERCENT_UNRESOLVED": 70,
        "REAL-07-SAFETY_PPE_UNAVAILABLE_OR_UNSUITABLE": 92,
        "REAL-08-TEMPORARY_DAY_TO_THREE_SHIFT_REFUSAL": 92,
        "REAL-09-CHEMICAL_RECIPE_OUTDATED_PROCEDURE": 74,
        "REAL-10-POSITIVE_ALCOHOL_TEST_HIGH_RISK_POSITION": 90,
        "REAL-11-INSULTS_SUPERVISOR_FATIGUE_CONTEXT": 82,
    }

    for fixture in fixtures:
        core = build_case_factual_core(
            build_case_prompt(fixture),
            str(
                fixture["case_input"].get("requested_path")
                or ROUTE_BY_CASE[fixture["case_id"]]
            ),
        )
        assert bool(core.blocking_ambiguities) is (
            fixture["case_id"]
            in {
                "REAL-05-DELEGATION_HOURS_CSSCT_INCOMPLETE",
                "REAL-06-ANNUAL_LEAVE_TEN_PERCENT_UNRESOLVED",
            }
        )
