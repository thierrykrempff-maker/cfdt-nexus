from __future__ import annotations

import re

import pytest

from SYNDICAL_REASONING_ENGINE import (
    WorkingTimeReasoningEngine,
    WorkingTimeSituation,
    working_time_scenarios,
)


@pytest.fixture(scope="module")
def results():
    engine = WorkingTimeReasoningEngine()
    return {
        code: engine.analyze(case, scenario_code=code)
        for code, case in working_time_scenarios().items()
    }


def test_exactly_ten_required_scenarios_exist():
    assert set(working_time_scenarios()) == {
        "daily_rest_recall",
        "contested_overtime",
        "night_work",
        "on_call_intervention",
        "five_shift",
        "apparently_missing_bonus",
        "kelio_nibelis_gap",
        "collective_organization",
        "interrupted_break",
        "cse_meeting_on_rest",
    }


def test_daily_rest_recall_is_urgent_and_requests_timing(results):
    result = results["daily_rest_recall"]
    assert WorkingTimeSituation.RECALL_DURING_REST in result.situations
    assert WorkingTimeSituation.DAILY_REST in result.situations
    assert any(item.urgency.value == "urgent" for item in result.qualifications)
    assert "repos suivant" in result.missing_information


def test_contested_overtime_compares_planning_badges_and_kelio(results):
    result = results["contested_overtime"]
    codes = {item.comparison_code for item in result.comparisons}
    assert {"schedule_timeclock", "schedule_kelio"} <= codes
    assert WorkingTimeSituation.OVERTIME in result.situations


def test_on_call_separates_period_intervention_travel_and_rest(results):
    situations = set(results["on_call_intervention"].situations)
    assert {
        WorkingTimeSituation.ON_CALL,
        WorkingTimeSituation.ON_CALL_INTERVENTION,
        WorkingTimeSituation.INTERVENTION_TRAVEL,
        WorkingTimeSituation.DAILY_REST,
    } <= situations


def test_five_shift_covers_cycle_breaks_rest_holidays_night_and_potential_bonus(results):
    result = results["five_shift"]
    assert {
        WorkingTimeSituation.FIVE_SHIFT,
        WorkingTimeSituation.WORK_CYCLE,
        WorkingTimeSituation.BREAK,
        WorkingTimeSituation.PUBLIC_HOLIDAY,
        WorkingTimeSituation.NIGHT_WORK,
        WorkingTimeSituation.POTENTIAL_PAY_IMPACT,
    } <= set(result.situations)


def test_missing_bonus_and_kelio_nibelis_gap_remain_anomalies_to_check(results):
    for code in ("apparently_missing_bonus", "kelio_nibelis_gap"):
        payload = results[code].to_dict()
        rendered = str(payload).lower()
        assert "erreur certaine" not in rendered
        assert "incohérence apparente à vérifier" in rendered
        alternatives = {
            item
            for comparison in results[code].comparisons
            for item in comparison.alternative_explanations
        }
        assert {"décalage de paie", "période de clôture", "régularisation ultérieure", "erreur de saisie", "paramétrage", "événement non validé"} <= alternatives


def test_collective_organization_articulates_r1a_then_r1c(results):
    articulation = results["collective_organization"].articulation
    assert articulation.primary_domain == "R1A_CONTRACT_CHANGE"
    assert articulation.complementary_domains == ("R1C_WORKING_TIME",)


def test_interrupted_break_and_cse_meeting_keep_notions_separate(results):
    interrupted = set(results["interrupted_break"].situations)
    assert WorkingTimeSituation.INTERRUPTED_BREAK in interrupted
    meeting = set(results["cse_meeting_on_rest"].situations)
    assert WorkingTimeSituation.REPRESENTATIVE_MEETING_ON_REST in meeting
    assert WorkingTimeSituation.DAILY_REST not in meeting


def test_all_scenarios_are_deterministic_synthetic_and_confidential(results):
    engine = WorkingTimeReasoningEngine()
    for code, case in working_time_scenarios().items():
        assert engine.analyze(case, scenario_code=code) == results[code]
        rendered = str(results[code].to_dict()).lower()
        for forbidden in ("fulltext", "local_path", "chunk_id", "matricule", "iban", "nir"):
            assert re.search(rf"\b{forbidden}\b", rendered) is None
        assert all("synth" in item.title.lower() for item in case.available_pieces)
