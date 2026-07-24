from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from EXPERT_PAIE_V2 import (
    ExpertPaieV2Engine,
    PayrollNormalizationError,
    PayrollPhase,
    RuleStatus,
    Unit,
    decimal_value,
    expert_paie_v2_scenarios,
    iso_date,
    normalize_value,
)


def analyze(code):
    return ExpertPaieV2Engine().analyze(
        expert_paie_v2_scenarios()[code], scenario_code=code
    )


def test_normalization_preserves_decimal_unit_and_provenance():
    value = normalize_value("quantity", "2.50", Unit.HOUR, "synthetic_planning")
    assert value.value == Decimal("2.50")
    assert value.unit is Unit.HOUR
    assert value.source == "synthetic_planning"
    assert iso_date("2026-01-31", field="date") == "2026-01-31"


@pytest.mark.parametrize("value", [True, "not-a-number", "NaN", "Infinity"])
def test_normalization_rejects_ambiguous_or_invalid_values(value):
    with pytest.raises(PayrollNormalizationError):
        decimal_value(value, field="amount")


def test_rule_selection_is_explainable_and_source_aware():
    result = analyze("compliant_case")
    assert result.rule_selections[0].selected
    assert result.rule_selections[0].source_rank == 0
    assert result.rule_selections[0].reasons


def test_to_verify_rule_refuses_calculation_explicitly():
    result = analyze("to_verify_rule")
    assert result.phase is PayrollPhase.CALCULATION_REFUSED
    assert "RULE_NOT_ACTIVE" in {item.code for item in result.refusals}
    assert result.calculation is None


def test_calculation_allowed_false_is_blocking():
    result = analyze("calculation_forbidden")
    assert "CALCULATION_NOT_ALLOWED" in {item.code for item in result.refusals}
    assert result.calculation is None


def test_missing_variable_and_incompatible_units_are_blocking():
    assert "MISSING_VARIABLES" in {item.code for item in analyze("missing_variable").refusals}
    assert "INCOMPATIBLE_UNITS" in {item.code for item in analyze("incompatible_units").refusals}


def test_authorized_calculation_uses_decimal_and_records_rounding():
    result = analyze("compliant_case")
    assert result.phase is PayrollPhase.AUTHORIZED_CALCULATION
    assert result.calculation.result == Decimal("25.00")
    assert result.calculation.rounding == "ROUND_HALF_UP to 0.01"
    assert result.calculation.steps


def test_comparisons_distinguish_delay_from_apparent_anomaly():
    delay = analyze("payroll_delay")
    assert any(item.status.value == "no_anomaly_detected" for item in delay.comparisons)
    missing = analyze("missing_overtime")
    assert any(item.status.value == "possible_anomaly" for item in missing.comparisons)
    assert len(missing.alternative_explanations) >= 2


def test_explanations_questions_evidence_strategies_and_articulation():
    result = analyze("collective_anomaly")
    assert result.employee_explanation
    assert result.expert_explanation
    assert {item.priority.value for item in result.questions} >= {"critical", "priority", "useful"}
    assert {item.priority.value for item in result.evidence} == {"essential", "useful", "complementary"}
    assert [item.level for item in result.strategies] == [1, 2, 3, 4, 5]
    assert any("R2C" in item for item in result.articulation)


def test_models_are_immutable_and_serializable():
    result = analyze("compliant_case")
    with pytest.raises(FrozenInstanceError):
        result.phase = PayrollPhase.CONTROL
    assert result.to_dict()["analysis_type"] == "expert_paie_v2_control"


def test_no_error_is_declared_certain():
    rendered = str(analyze("missing_overtime").to_dict()).lower()
    assert "erreur de paie certaine" not in rendered
    assert "anomalie certaine" not in rendered
