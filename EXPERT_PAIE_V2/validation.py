"""Blocking validation before any synthetic calculation."""

from __future__ import annotations

from .models import CalculationRefusal, PayrollRule, PayrollV2Input, RuleStatus
from .normalization import PayrollNormalizationError, values_by_name


def validate_calculation(
    payload: PayrollV2Input,
    rule: PayrollRule | None,
    *,
    applicable_rule_count: int = 1,
) -> tuple[CalculationRefusal, ...]:
    refusals = []
    if rule is None:
        return (_refusal("NO_APPLICABLE_RULE", "aucune règle applicable validée", (), None),)
    if rule.status is not RuleStatus.ACTIVE:
        refusals.append(_refusal("RULE_NOT_ACTIVE", f"règle {rule.status.value}", (), rule.rule_id))
    if not rule.calculation_allowed:
        refusals.append(_refusal("CALCULATION_NOT_ALLOWED", "calculation_allowed = false", (), rule.rule_id))
    if applicable_rule_count > 1:
        refusals.append(
            _refusal(
                "INCOMPATIBLE_RULES",
                "plusieurs règles incompatibles restent possibles",
                (),
                rule.rule_id,
            )
        )
    if payload.period is None or not payload.period.clearly_defined:
        refusals.append(_refusal("AMBIGUOUS_PERIOD", "période de paie ambiguë", ("période",), rule.rule_id))
    if payload.contradictory_data:
        refusals.append(_refusal("CRITICAL_CONTRADICTION", "donnée critique contradictoire", (), rule.rule_id))
    if not payload.confidentiality_validated:
        refusals.append(_refusal("CONFIDENTIALITY_NOT_VALIDATED", "confidentialité non assurée", (), rule.rule_id))
    try:
        values = values_by_name((*payload.planning_values, *payload.parameters))
    except PayrollNormalizationError:
        refusals.append(_refusal("INCOMPATIBLE_VALUES", "valeurs contradictoires", (), rule.rule_id))
        values = {}
    missing = tuple(name for name in (*rule.required_variables, *rule.required_parameters) if name not in values or values[name].value is None)
    if missing:
        refusals.append(_refusal("MISSING_VARIABLES", "variables obligatoires manquantes", missing, rule.rule_id))
    incompatible = (
        ("base" in values and values["base"].unit.value != "amount")
        or ("quantity" in values and values["quantity"].unit.value not in {"hour", "day", "count"})
        or ("rate" in values and values["rate"].unit.value != "rate")
    )
    if incompatible:
        refusals.append(_refusal("INCOMPATIBLE_UNITS", "unités incompatibles", (), rule.rule_id))
    return tuple(refusals)


def _refusal(code: str, reason: str, missing: tuple[str, ...], rule_id: str | None) -> CalculationRefusal:
    return CalculationRefusal(
        code,
        reason,
        missing,
        tuple("document:" + item for item in missing) or ("règle et pièces applicables",),
        rule_id,
        "compléter et faire vérifier les données avant tout calcul",
    )
