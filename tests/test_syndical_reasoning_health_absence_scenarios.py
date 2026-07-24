from __future__ import annotations

import pytest

from SYNDICAL_REASONING_ENGINE import (
    HealthAbsenceReasoningEngine,
    HealthSituation,
    health_absence_scenarios,
)


EXPECTED = {
    "sick_leave_maintenance": HealthSituation.SALARY_MAINTENANCE,
    "missing_ijss": HealthSituation.DAILY_ALLOWANCE,
    "work_accident_pending": HealthSituation.REPORTED_WORK_ACCIDENT,
    "employer_reservations": HealthSituation.EMPLOYER_RESERVATIONS,
    "return_without_visit": HealthSituation.RETURN_VISIT,
    "therapeutic_part_time": HealthSituation.THERAPEUTIC_PART_TIME,
    "adjustment_refused": HealthSituation.WORK_ADJUSTMENT,
    "unfitness_redeployment": HealthSituation.REPORTED_UNFITNESS,
    "no_redeployment_offer": HealthSituation.REDEPLOYMENT,
    "provident_not_opened": HealthSituation.PROVIDENT_COVER,
    "mutual_portability": HealthSituation.PORTABILITY,
    "leave_and_sickness": HealthSituation.LEAVE_COUNTER_IMPACT,
    "absence_discipline": HealthSituation.POTENTIALLY_UNJUSTIFIED_ABSENCE,
    "duties_removed_after_leave": HealthSituation.POSSIBLE_HEALTH_DISCRIMINATION,
    "possible_occupational_unfitness": HealthSituation.REPORTED_UNFITNESS,
}


@pytest.mark.parametrize("scenario_code", tuple(EXPECTED))
def test_fifteen_required_scenarios_are_complete(scenario_code):
    case = health_absence_scenarios()[scenario_code]
    result = HealthAbsenceReasoningEngine().analyze(case, scenario_code=scenario_code)
    assert EXPECTED[scenario_code] in result.situations
    assert result.scenario_code == scenario_code
    assert result.qualifications
    assert result.actors
    assert result.automatic_questions
    assert result.evidence
    assert result.comparisons
    assert len(result.strategies) == 5


def test_work_accident_stays_pending_until_cpam_decision():
    result = HealthAbsenceReasoningEngine().analyze(health_absence_scenarios()["work_accident_pending"])
    rendered = str(result.to_dict()).lower()
    assert "occupational_recognition_pending" in rendered
    assert "reconnaissance acquise" not in rendered


def test_therapeutic_part_time_contains_no_amount():
    result = HealthAbsenceReasoningEngine().analyze(health_absence_scenarios()["therapeutic_part_time"])
    assert all(item.calculation_performed is False for item in result.comparisons)


def test_absence_discipline_articulates_r1b_as_primary():
    result = HealthAbsenceReasoningEngine().analyze(health_absence_scenarios()["absence_discipline"])
    assert result.articulation.primary_domain == "R1B_DISCIPLINARY"
    assert "R1E_HEALTH_ABSENCE" in result.articulation.complementary_domains
