from __future__ import annotations

import pytest

from SYNDICAL_REASONING_ENGINE import (
    CSEAlertsExpertiseReasoningEngine,
    cse_alerts_scenarios,
)


EXPECTED = {
    "similar_counter_claims",
    "collective_union_discrimination",
    "individual_rights",
    "potential_economic_alert",
    "temporary_work_increase",
    "recurring_understaffing",
    "potential_economic_expertise",
    "important_project",
    "disputed_expertise",
    "documents_refused",
    "unmet_commitment",
    "investigation_request",
    "labour_inspectorate",
    "defender_of_rights",
    "isolated_individual",
    "corrected_situation",
    "insufficient_alert",
    "extraordinary_meeting",
    "expertise_resolution",
    "possible_obstruction",
}


def test_exactly_twenty_required_synthetic_scenarios_exist():
    scenarios = cse_alerts_scenarios()
    assert set(scenarios) == EXPECTED
    assert len(scenarios) == 20


@pytest.mark.parametrize("code", sorted(EXPECTED))
def test_every_scenario_is_deterministic_metadata_only_and_prudent(code):
    engine = CSEAlertsExpertiseReasoningEngine()
    case = cse_alerts_scenarios()[code]
    first = engine.analyze(case, scenario_code=code).to_dict()
    second = engine.analyze(case, scenario_code=code).to_dict()
    assert first == second
    assert first["scenario_code"] == code
    rendered = str(first).lower()
    assert "fictif" in str(case).lower() or "synthétique" in str(case).lower()
    for forbidden in ("pdf", "html", "fulltext", "chunk_id", "storage_id", "vrai pv", "vraie alerte"):
        assert forbidden not in rendered


def test_articulation_preserves_r2a_r2b_and_r1_responsibilities():
    analyses = {
        code: CSEAlertsExpertiseReasoningEngine().analyze(case)
        for code, case in cse_alerts_scenarios().items()
    }
    assert analyses["important_project"].articulation.primary_domain == "R2A_CSE_CONSULTATION"
    assert "R2B_CSE_OPERATION" in analyses["important_project"].articulation.complementary_domains
    assert "R1C_WORKING_TIME" in analyses["similar_counter_claims"].articulation.complementary_domains
    assert "R1D_DISCRIMINATION_HARASSMENT" in analyses["collective_union_discrimination"].articulation.complementary_domains
    assert analyses["isolated_individual"].articulation.primary_domain.startswith("R1")
