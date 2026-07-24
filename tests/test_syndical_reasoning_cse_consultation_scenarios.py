from __future__ import annotations

import pytest

from SYNDICAL_REASONING_ENGINE import (
    CSEConsultationReasoningEngine,
    CollectiveDimension,
    cse_consultation_scenarios,
)


EXPECTED = {
    "laboratory",
    "job_suppression",
    "collective_schedule",
    "monitoring_tool",
    "outsourcing",
    "employees_informed_first",
    "implementation_before_opinion",
    "insufficient_documents",
    "isolated_individual",
    "repeated_individual",
    "historical_commitment",
    "economic_project",
    "document_refusal",
    "regular_consultation",
    "obstruction_risk",
}


def test_all_required_scenarios_exist():
    assert set(cse_consultation_scenarios()) == EXPECTED


@pytest.mark.parametrize("scenario_code", sorted(EXPECTED))
def test_every_scenario_produces_a_complete_deterministic_analysis(scenario_code):
    case = cse_consultation_scenarios()[scenario_code]
    engine = CSEConsultationReasoningEngine()
    first = engine.analyze(case, scenario_code=scenario_code)
    second = engine.analyze(case, scenario_code=scenario_code)
    assert first.to_dict() == second.to_dict()
    assert first.qualifications
    assert first.automatic_questions
    assert first.document_requests
    assert len(first.strategies) == 5
    assert first.scenario_code == scenario_code


def test_repeated_cases_are_not_automatically_declared_a_project():
    result = CSEConsultationReasoningEngine().analyze(
        cse_consultation_scenarios()["repeated_individual"]
    )
    assert result.collective_dimension is CollectiveDimension.REPEATED_INDIVIDUAL_CASES
    assert all("établie" not in item.label for item in result.qualifications)


def test_health_safety_boundary_is_not_cssct_reasoning():
    result = CSEConsultationReasoningEngine().analyze(
        cse_consultation_scenarios()["monitoring_tool"]
    )
    rendered = str(result.to_dict()).lower()
    assert "expertise cssct" not in rendered
    assert "analyse cssct approfondie" not in rendered
