"""Explainable payroll-rule selection."""

from __future__ import annotations

from .models import PayrollEvent, PayrollRule, RuleSelection, RuleStatus


SOURCE_RANK = {
    "accord_ineos": 0,
    "convention_collective": 1,
    "code_travail": 2,
    "parametre_officiel": 3,
    "regle_interne_validee": 4,
}


def select_rules(
    events: tuple[PayrollEvent, ...], rules: tuple[PayrollRule, ...]
) -> tuple[RuleSelection, ...]:
    event_types = {item.event_type for item in events}
    decisions = []
    for rule in rules:
        reasons = []
        exclusions = []
        if not event_types.intersection(rule.event_types):
            exclusions.append("event type does not match")
        else:
            reasons.append("event type matches")
        if rule.source_layer not in SOURCE_RANK:
            exclusions.append("source hierarchy is unknown")
        else:
            reasons.append(f"source rank {SOURCE_RANK[rule.source_layer]}")
        if rule.status is not RuleStatus.ACTIVE:
            exclusions.append(f"rule status is {rule.status.value}")
        selected = not exclusions
        decisions.append(
            RuleSelection(
                rule.rule_id,
                rule.title,
                selected,
                tuple(reasons),
                tuple(exclusions),
                bool(selected and rule.calculation_allowed),
                SOURCE_RANK.get(rule.source_layer, 99),
            )
        )
    return tuple(sorted(decisions, key=lambda item: (not item.selected, item.source_rank, item.rule_id)))


def selected_rule(
    rules: tuple[PayrollRule, ...], selections: tuple[RuleSelection, ...]
) -> PayrollRule | None:
    selected_ids = [item.rule_id for item in selections if item.selected]
    if not selected_ids:
        return None
    by_id = {item.rule_id: item for item in rules}
    return by_id[selected_ids[0]]
