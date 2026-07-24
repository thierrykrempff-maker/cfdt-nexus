"""Strict Decimal-only synthetic calculation."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .models import CalculationTrace, ConfidenceLevel, PayrollRule, PayrollV2Input, Unit
from .normalization import values_by_name


def calculate(payload: PayrollV2Input, rule: PayrollRule) -> CalculationTrace:
    values = values_by_name((*payload.planning_values, *payload.parameters))
    base = values["base"].value
    quantity = values["quantity"].value
    rate = values["rate"].value
    if base is None or quantity is None or rate is None:
        raise ValueError("calculation variables are missing")
    raw = base * quantity * rate
    result = raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return CalculationTrace(
        rule.rule_id,
        base,
        quantity,
        rate,
        rule.formula or "base * quantity * rate",
        (f"base={base}", f"quantity={quantity}", f"rate={rate}", f"raw={raw}", f"rounded={result}"),
        result,
        Unit.AMOUNT,
        "ROUND_HALF_UP to 0.01",
        ConfidenceLevel.HIGH,
        ("résultat synthétique à valider humainement",),
        (rule.source,),
    )
