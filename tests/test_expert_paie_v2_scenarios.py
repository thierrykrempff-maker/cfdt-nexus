from __future__ import annotations

import pytest

from EXPERT_PAIE_V2 import ExpertPaieV2Engine, expert_paie_v2_scenarios


EXPECTED = {
    "missing_overtime",
    "payroll_delay",
    "on_call_without_intervention",
    "on_call_with_intervention",
    "night_work",
    "sunday_or_holiday",
    "missing_shift_premium",
    "kelio_nibelis_mismatch",
    "to_verify_rule",
    "calculation_forbidden",
    "missing_variable",
    "incompatible_units",
    "salary_maintenance",
    "ijss_subrogation",
    "potential_provident",
    "regularization",
    "unpaid_absence",
    "leave_or_rtt",
    "compliant_case",
    "collective_anomaly",
}


def test_exactly_twenty_required_synthetic_scenarios_exist():
    assert set(expert_paie_v2_scenarios()) == EXPECTED


@pytest.mark.parametrize("code", sorted(EXPECTED))
def test_scenarios_are_deterministic_synthetic_and_explainable(code):
    engine = ExpertPaieV2Engine()
    payload = expert_paie_v2_scenarios()[code]
    first = engine.analyze(payload, scenario_code=code).to_dict()
    second = engine.analyze(payload, scenario_code=code).to_dict()
    assert first == second
    assert payload.employee.synthetic
    assert first["scenario_code"] == code
    assert first["employee_explanation"]
    assert first["expert_explanation"]


def test_events_cover_required_payroll_families():
    event_types = {
        event.event_type.value
        for payload in expert_paie_v2_scenarios().values()
        for event in payload.events
    }
    assert {
        "overtime",
        "night_work",
        "sunday_work",
        "shift_premium",
        "on_call",
        "on_call_intervention",
        "salary_maintenance",
        "subrogation",
        "provident",
        "regularization",
        "unpaid_absence",
        "rtt",
    } <= event_types
