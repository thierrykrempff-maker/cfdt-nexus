#!/usr/bin/env python
"""Integration tests for LOT 4H inside the payroll expert."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from automation.experts import paie  # noqa: E402
from automation.payroll import payroll_referential_integration as integration  # noqa: E402


def answer(query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "query": query,
        "route": {"domains": ["paie_remuneration"]},
        "sources": [{"document": "Accord local de test", "source_layer": "accord_entreprise"}],
        "documents_to_request": [],
        "payroll_rule_context": context or {},
    }


def overtime_context(**overrides: Any) -> dict[str, Any]:
    context: dict[str, Any] = {
        "employee_population": "personnel concerne",
        "reference_date": "2026-06-30",
        "payroll_period": "juin 2026",
        "documents": ["bulletin de paie", "planning Kelio", "accord entreprise"],
        "variables": {"overtime_hours": 6},
    }
    context.update(overrides)
    return context


def lot4h(payload: dict[str, Any]) -> dict[str, Any]:
    analysis = payload.get("payroll_referential_analysis")
    assert isinstance(analysis, dict)
    return analysis


def test_protocol_is_integrated_with_all_twelve_steps() -> None:
    analysis = lot4h(paie.enrich(answer("Mes heures supplementaires ne sont pas payees.", overtime_context())))
    assert analysis["available"] is True
    assert len(analysis["protocol_steps"]) == 12
    assert analysis["protocol_steps"][0] == "understand_request"
    assert analysis["protocol_steps"][-1] == "produce_response"


def test_employee_response_is_simple_and_without_referential_jargon() -> None:
    payload = paie.enrich(answer("Mes heures supplementaires ne sont pas payees.", overtime_context()))
    analysis = lot4h(payload)
    response = analysis["employee_response"]
    assert payload["reponse_salarie"] == response
    assert response["audience"] == "employee"
    assert "message" in response and "explanation" in response
    assert "nibelis_rubrics" not in response and "graph_relations" not in response


def test_expert_response_contains_all_control_families() -> None:
    payload = paie.enrich(answer("Mes heures supplementaires ne sont pas payees.", overtime_context()))
    analysis = lot4h(payload)
    response = analysis["expert_response"]
    assert payload["reponse_expert"] == response
    assert response["audience"] == "expert"
    assert {
        "rules", "variables", "kelio_counters", "nibelis_rubrics", "parameters",
        "graph_relations", "documents_verified", "documents_missing", "confidence", "limits",
    }.issubset(response)


def test_referentials_and_graph_are_used_as_hints() -> None:
    analysis = lot4h(paie.enrich(answer("Mes heures supplementaires ne sont pas payees.", overtime_context())))
    candidates = analysis["referential_candidates"]
    assert candidates["kelio_counters"]
    assert candidates["nibelis_rubrics"]
    assert candidates["parameters"]
    assert candidates["graph_relations"]
    assert all(item["status"] == "synthetic_control_hint" for item in candidates["graph_relations"])
    assert all(item["calculation_allowed"] is False for item in candidates["graph_relations"])


def test_missing_indispensable_documents_interrupts_and_requests_them() -> None:
    context = overtime_context(documents=[])
    analysis = lot4h(paie.enrich(answer("Mes heures supplementaires ne sont pas payees.", context)))
    assert analysis["interrupted"] is True
    assert {"kelio", "payslip"}.issubset(set(analysis["documents_missing"]))
    assert analysis["employee_response"]["message"] == "Impossible de conclure avec certitude."
    assert analysis["employee_response"]["documents_to_provide"]


def test_low_confidence_causes_are_explicit() -> None:
    payload = paie.enrich(answer("Mes heures supplementaires ne sont pas payees.", {}))
    analysis = lot4h(payload)
    assert analysis["confidence"] == "LOW"
    assert payload["niveau_de_confiance"] == "LOW"
    assert analysis["confidence_reasons"]
    assert analysis["refusal_reasons"]


def test_existing_calculation_refusal_is_maintained() -> None:
    payload = paie.enrich(answer("Mes heures supplementaires ne sont pas payees.", overtime_context()))
    assert payload["payroll_rule_analysis"]["calculation_ready"] is False
    assert payload["calcul_detaille"].startswith("Non produit")
    assert lot4h(payload)["calculation_performed"] is False


def test_no_synthetic_value_is_used_and_no_engine_is_imported() -> None:
    source = inspect.getsource(integration)
    assert "payroll_rule_engine" not in source
    analysis = lot4h(paie.enrich(answer("Mes heures supplementaires ne sont pas payees.", overtime_context())))
    assert analysis["synthetic_values_used"] is False
    serialized = repr(analysis["referential_candidates"])
    assert "synthetic_reading_examples" not in serialized
    assert "current_value" not in serialized and "fallback_value" not in serialized


def test_contradictory_documents_maintain_refusal() -> None:
    context = overtime_context(contradictory_documents=True)
    analysis = lot4h(paie.enrich(answer("Mes heures supplementaires ne sont pas payees.", context)))
    assert analysis["interrupted"] is True
    assert any("contradictoires" in reason for reason in analysis["refusal_reasons"])


def test_integration_failure_preserves_legacy_expert_payload() -> None:
    previous = integration.load_safe_catalogs

    def broken_catalogs() -> dict[str, dict[str, Any]]:
        raise ValueError("catalogue indisponible de test")

    integration.load_safe_catalogs = broken_catalogs
    try:
        payload = paie.enrich(answer("Mes heures supplementaires ne sont pas payees.", overtime_context()))
    finally:
        integration.load_safe_catalogs = previous
    assert payload["active"] is True
    assert payload["elements_du_bulletin_concernes"]
    assert payload["payroll_rule_analysis"]
    assert lot4h(payload)["available"] is False


def test_non_payroll_scenario_keeps_existing_inactive_shape() -> None:
    payload = paie.enrich({"query": "Question sans rapport", "route": {"domains": []}})
    assert payload == {
        "active": False,
        "name": "Expert Paie V0",
        "reason": "Question hors perimetre paie pour cette orchestration.",
    }


def run_all() -> None:
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print(f"OK {name}")


if __name__ == "__main__":
    run_all()
