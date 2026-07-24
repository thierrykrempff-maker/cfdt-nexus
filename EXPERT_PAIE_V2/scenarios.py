"""Twenty anonymous and synthetic payroll-control scenarios."""

from __future__ import annotations

from decimal import Decimal

from .models import (
    KelioCounter,
    NibelisRubric,
    PayrollEvent,
    PayrollEventType,
    PayrollPeriod,
    PayrollRule,
    PayrollV2Input,
    PayrollValue,
    RuleStatus,
    SyntheticEmployee,
    Unit,
)


EMPLOYEE = SyntheticEmployee("SYNTHETIC-EMPLOYEE", "synthetic_shift")
PERIOD = PayrollPeriod("2026-01-01", "2026-01-31", "2026-01")


def _rule(event, *, status=RuleStatus.ACTIVE, allowed=False, variables=("base", "quantity", "rate")):
    return PayrollRule(
        f"SYN-{event.value}",
        f"Règle synthétique {event.value}",
        status,
        event.value,
        (event,),
        variables,
        (),
        "accord_ineos",
        "référentiel synthétique validé",
        1,
        allowed,
        "base * quantity * rate" if allowed else None,
    )


def _case(event, *, kelio=True, rubric=False, next_rubric=False, rule=None, values=(), collective=False):
    code = f"RUB-{event.value}"
    return PayrollV2Input(
        f"Contrôle synthétique fictif : {event.value}",
        PERIOD,
        EMPLOYEE,
        (PayrollEvent(event, "2026-01", Decimal("2"), Unit.HOUR, "synthetic_planning", code),),
        tuple(values),
        (KelioCounter(f"K-{event.value}", "2026-01", Decimal("2"), Unit.HOUR),) if kelio else (),
        (NibelisRubric(code, "2026-02" if next_rubric else "2026-01", Decimal("2"), Decimal("20")),) if rubric or next_rubric else (),
        (),
        (rule or _rule(event),),
        (),
        False,
        True,
        "collective" if collective else None,
    )


def expert_paie_v2_scenarios() -> dict[str, PayrollV2Input]:
    values = (
        PayrollValue("base", Decimal("10"), Unit.AMOUNT, "synthetic_parameter"),
        PayrollValue("quantity", Decimal("2"), Unit.HOUR, "synthetic_planning"),
        PayrollValue("rate", Decimal("1.25"), Unit.RATE, "synthetic_rule"),
    )
    overtime = PayrollEventType.OVERTIME
    return {
        "missing_overtime": _case(overtime),
        "payroll_delay": _case(overtime, rubric=False, next_rubric=True),
        "on_call_without_intervention": _case(PayrollEventType.ON_CALL),
        "on_call_with_intervention": _case(PayrollEventType.ON_CALL_INTERVENTION),
        "night_work": _case(PayrollEventType.NIGHT_WORK),
        "sunday_or_holiday": _case(PayrollEventType.SUNDAY_WORK),
        "missing_shift_premium": _case(PayrollEventType.SHIFT_PREMIUM),
        "kelio_nibelis_mismatch": _case(overtime, rubric=False),
        "to_verify_rule": _case(overtime, rule=_rule(overtime, status=RuleStatus.TO_VERIFY)),
        "calculation_forbidden": _case(overtime, rule=_rule(overtime, allowed=False)),
        "missing_variable": _case(overtime, rule=_rule(overtime, allowed=True), values=values[:2]),
        "incompatible_units": _case(overtime, rule=_rule(overtime, allowed=True), values=values[:-1] + (PayrollValue("rate", Decimal("1.25"), Unit.DAY, "synthetic_rule"),)),
        "salary_maintenance": _case(PayrollEventType.SALARY_MAINTENANCE),
        "ijss_subrogation": _case(PayrollEventType.SUBROGATION),
        "potential_provident": _case(PayrollEventType.PROVIDENT),
        "regularization": _case(PayrollEventType.REGULARIZATION, rubric=True),
        "unpaid_absence": _case(PayrollEventType.UNPAID_ABSENCE),
        "leave_or_rtt": _case(PayrollEventType.RTT),
        "compliant_case": _case(overtime, rubric=True, rule=_rule(overtime, allowed=True), values=values),
        "collective_anomaly": _case(overtime, collective=True),
    }
