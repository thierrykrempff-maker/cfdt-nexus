from __future__ import annotations

import pytest

from SYNDICAL_REASONING_ENGINE import (
    DiscriminationHarassmentReasoningEngine,
    SituationType,
    UrgencyLevel,
    discrimination_harassment_scenarios,
)


EXPECTED = {
    "possible_moral_harassment": SituationType.POSSIBLE_MORAL_HARASSMENT,
    "isolated_conflict": SituationType.ISOLATED_INAPPROPRIATE_BEHAVIOUR,
    "possible_sexual_harassment": SituationType.POSSIBLE_SEXUAL_HARASSMENT,
    "union_discrimination": SituationType.POSSIBLE_DISCRIMINATION,
    "equal_pay": SituationType.DIFFERENCE_IN_TREATMENT,
    "health_return": SituationType.POSSIBLE_DISCRIMINATION,
    "retaliation": SituationType.POSSIBLE_RETALIATION,
    "different_sanctions": SituationType.DIFFERENCE_IN_TREATMENT,
    "sexist_behaviour": SituationType.SEXIST_BEHAVIOUR,
    "insufficient_evidence": SituationType.INSUFFICIENT_FACTS,
    "representative_isolated": SituationType.POSSIBLE_UNION_RIGHTS_INTERFERENCE,
    "immediate_danger": SituationType.PROTECTION_URGENCY,
}


@pytest.mark.parametrize("scenario_code", tuple(EXPECTED))
def test_twelve_required_scenarios_are_complete_and_prudent(scenario_code):
    case = discrimination_harassment_scenarios()[scenario_code]
    result = DiscriminationHarassmentReasoningEngine().analyze(
        case, scenario_code=scenario_code
    )
    assert EXPECTED[scenario_code] in {item.situation for item in result.hypotheses}
    assert result.scenario_code == scenario_code
    assert result.automatic_questions
    assert result.evidence
    assert result.comparators
    assert len(result.strategies) == 5
    assert result.confidence.value in {"low", "moderate"}


def test_isolated_conflict_never_becomes_possible_moral_harassment_automatically():
    result = DiscriminationHarassmentReasoningEngine().analyze(
        discrimination_harassment_scenarios()["isolated_conflict"]
    )
    situations = {item.situation for item in result.hypotheses}
    assert SituationType.POSSIBLE_MORAL_HARASSMENT not in situations
    assert SituationType.PROFESSIONAL_CONFLICT in situations


def test_health_scenario_contains_no_medical_inference():
    result = DiscriminationHarassmentReasoningEngine().analyze(
        discrimination_harassment_scenarios()["health_return"]
    )
    rendered = str(result.to_dict()).lower()
    assert "dépression diagnostiquée" not in rendered
    assert "maladie déduite" not in rendered
    assert "pathologie établie" not in rendered


def test_immediate_danger_prioritizes_protection():
    result = DiscriminationHarassmentReasoningEngine().analyze(
        discrimination_harassment_scenarios()["immediate_danger"]
    )
    assert result.urgency is UrgencyLevel.IMMEDIATE
    assert result.strategies[0].name == "Sécurisation"
