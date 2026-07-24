"""Structured planning, Kelio, Nibelis and payroll comparisons."""

from __future__ import annotations

from .models import (
    ComparisonStatus,
    ConfidenceLevel,
    PayrollComparison,
    PayrollEventType,
    PayrollRule,
    PayrollV2Input,
)


def compare_payload(
    payload: PayrollV2Input, rule: PayrollRule | None = None
) -> tuple[PayrollComparison, ...]:
    results = []
    for event in payload.events:
        kelio = [item for item in payload.kelio_counters if item.period == event.date_or_period]
        rubrics = [item for item in payload.nibelis_rubrics if item.period == event.date_or_period]
        next_month = [item for item in payload.nibelis_rubrics if item.period != event.date_or_period]
        if event.quantity is None:
            status = ComparisonStatus.INSUFFICIENT_DATA
        elif not kelio:
            status = ComparisonStatus.POSSIBLE_ANOMALY
        elif any(item.quantity == event.quantity and item.unit is event.unit for item in kelio):
            status = ComparisonStatus.MATCH
        else:
            status = ComparisonStatus.APPARENT_DIFFERENCE
        results.append(
            PayrollComparison(
                "planning_kelio",
                f"{event.quantity} {event.unit.value}",
                ", ".join(f"{item.quantity} {item.unit.value}" for item in kelio) or "absent",
                None if status is ComparisonStatus.MATCH else "quantité ou présence à vérifier",
                status,
                ("correction de compteur", "période différente", "événement non validé"),
                ConfidenceLevel.MODERATE,
            )
        )
        if event.expected_rubric:
            current = [item for item in rubrics if item.rubric_code == event.expected_rubric]
            later = [item for item in next_month if item.rubric_code == event.expected_rubric]
            rubric_status = (
                ComparisonStatus.MATCH if current
                else ComparisonStatus.NO_ANOMALY_DETECTED if later
                else ComparisonStatus.POSSIBLE_ANOMALY
            )
            alternatives = ("décalage de paie documenté",) if later else ("décalage de paie possible", "rubrique différente à confirmer", "régularisation ultérieure")
            results.append(
                PayrollComparison(
                    "kelio_nibelis",
                    event.expected_rubric,
                    current[0].rubric_code if current else later[0].rubric_code if later else "absent",
                    None if current or later else "rubrique potentiellement absente",
                    rubric_status,
                    alternatives,
                    ConfidenceLevel.HIGH if current or later else ConfidenceLevel.MODERATE,
                )
            )
        if rule is not None and event.event_type in rule.event_types:
            observed = [item.rubric_code for item in rubrics]
            status = (
                ComparisonStatus.MATCH
                if event.expected_rubric and event.expected_rubric in observed
                else ComparisonStatus.POSSIBLE_ANOMALY
                if event.expected_rubric
                else ComparisonStatus.INSUFFICIENT_DATA
            )
            results.append(
                PayrollComparison(
                    "rule_observed_treatment",
                    f"rule={rule.rule_id}; expected={event.expected_rubric or 'to determine'}",
                    ",".join(observed) or "no observed rubric",
                    None if status is ComparisonStatus.MATCH else "application et période à vérifier",
                    status,
                    ("rubrique différente", "décalage de paie", "règle concurrente"),
                    ConfidenceLevel.MODERATE,
                )
            )
    health_types = {
        PayrollEventType.SICKNESS,
        PayrollEventType.WORK_ACCIDENT,
        PayrollEventType.SALARY_MAINTENANCE,
        PayrollEventType.IJSS,
        PayrollEventType.SUBROGATION,
        PayrollEventType.PROVIDENT,
    }
    if any(item.event_type in health_types for item in payload.events):
        observed_codes = tuple(item.rubric_code for item in payload.nibelis_rubrics)
        results.append(
            PayrollComparison(
                "ijss_salary_maintenance_subrogation",
                "périodes IJSS, maintien, subrogation et prévoyance à rapprocher",
                ", ".join(observed_codes) or "aucun flux suffisamment documenté",
                "décalage ou articulation impossible à conclure"
                if not observed_codes
                else None,
                ComparisonStatus.INSUFFICIENT_DATA
                if not observed_codes
                else ComparisonStatus.APPARENT_DIFFERENCE,
                (
                    "décalage de versement",
                    "subrogation à confirmer",
                    "dossier prévoyance potentiel sans promesse de garantie",
                ),
                ConfidenceLevel.LOW if not observed_codes else ConfidenceLevel.MODERATE,
            )
        )
    return tuple(results)
