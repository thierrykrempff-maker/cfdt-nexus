"""Strict normalization without silent correction."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from .models import PayrollValue, Unit


class PayrollNormalizationError(ValueError):
    pass


def decimal_value(value: object, *, field: str) -> Decimal:
    if isinstance(value, bool):
        raise PayrollNormalizationError(f"{field}: boolean is not a payroll number")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise PayrollNormalizationError(f"{field}: invalid decimal") from None
    if not result.is_finite():
        raise PayrollNormalizationError(f"{field}: non-finite decimal")
    return result


def iso_date(value: str, *, field: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        raise PayrollNormalizationError(f"{field}: invalid ISO date") from None


def normalize_value(
    name: str,
    value: object,
    unit: Unit | str,
    source: str,
    *,
    period: str | None = None,
    certain: bool = True,
) -> PayrollValue:
    if not source.strip():
        raise PayrollNormalizationError(f"{name}: provenance is required")
    try:
        normalized_unit = unit if isinstance(unit, Unit) else Unit(unit)
    except ValueError:
        raise PayrollNormalizationError(f"{name}: unsupported unit") from None
    normalized = None if value is None else decimal_value(value, field=name)
    return PayrollValue(name, normalized, normalized_unit, source, period, certain)


def values_by_name(values: tuple[PayrollValue, ...]) -> dict[str, PayrollValue]:
    result: dict[str, PayrollValue] = {}
    for item in values:
        if item.name in result and result[item.name] != item:
            raise PayrollNormalizationError(f"{item.name}: contradictory values")
        result[item.name] = item
    return result
