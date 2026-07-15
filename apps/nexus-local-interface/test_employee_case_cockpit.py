#!/usr/bin/env python
"""Backend and static frontend tests for Cockpit V3 employee cases."""

from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parents[1]
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(ROOT))

import server as server_module  # noqa: E402
from employee_case_demo import SCENARIOS, build_demo_payload, public_scenarios  # noqa: E402


@contextmanager
def local_server() -> Iterator[str]:
    server = server_module.ThreadingHTTPServer(("127.0.0.1", 0), server_module.NexusHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def get_json(url: str) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - localhost only.
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def app_source(name: str) -> str:
    return (APP_DIR / name).read_text(encoding="utf-8")


def test_scenarios_endpoint_is_available_and_excludes_privacy_probe() -> None:
    with local_server() as base:
        status, payload = get_json(base + "/api/employee-case/scenarios")
    assert status == 200 and payload["ok"] is True
    assert len(payload["scenarios"]) == 5
    assert all("privacy" not in item["id"] for item in payload["scenarios"])


def test_demo_endpoint_returns_json_serializable_backend_structures() -> None:
    with local_server() as base:
        status, payload = get_json(base + "/api/employee-case/demo?scenario=overtime-complete")
    assert status == 200 and payload["ok"] is True
    json.dumps(payload, ensure_ascii=False)
    assert payload["case"]["case_id"] == "CASE_OVERTIME_SYN_001"


def test_unknown_case_returns_not_found_without_fake_data() -> None:
    with local_server() as base:
        status, payload = get_json(base + "/api/employee-case/demo?scenario=unknown")
    assert status == 404
    assert payload == {"ok": False, "error": "Dossier synthetique inconnu."}


def test_all_public_scenarios_are_generated_by_pipeline_and_report() -> None:
    assert len(public_scenarios()) == 5
    for scenario_id in SCENARIOS:
        payload = build_demo_payload(scenario_id)
        assert len(payload["pipeline"]["steps"]) == 12
        assert payload["employee_view"] == payload["report"]["employee_view"]
        assert payload["expert_view"] == payload["report"]["expert_view"]
        assert payload["report_metadata"] == payload["report"]["sections"]["metadata"]


def test_blocked_theme_is_preserved_without_blocking_other_display_data() -> None:
    payload = build_demo_payload("on-call-incomplete")
    assert payload["themes_blocked"] == ["on_call"]
    assert payload["report"]["sections"]["theme_analysis"][0]["status"] == "blocked"
    assert payload["pipeline"]["steps"]


def test_contradictions_are_preserved() -> None:
    payload = build_demo_payload("sickness-contradictory")
    assert payload["contradictions"]
    assert any("absence_period" in item for item in payload["contradictions"])


def test_unavailable_expert_status_is_preserved() -> None:
    payload = build_demo_payload("classification-missing-job")
    summary = payload["report"]["sections"]["payroll_expert_summary"]
    assert "unavailable" in summary["status"]
    assert summary["refusals"] == ["Expert Paie indisponible pour ce scenario."]


def test_payload_exposes_no_parameter_value_sensitive_probe_or_calculation() -> None:
    payload = build_demo_payload("paid-leave-complete")
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    assert "numeric_value" not in serialized and "parameter_value" not in serialized
    assert "privacy_probe" not in serialized
    assert payload["calculation_performed"] is False
    assert payload["report"]["calculation_performed"] is False


def test_endpoint_failure_is_explicit_and_safe() -> None:
    previous = server_module.build_demo_payload

    def broken_demo(_scenario: str) -> dict[str, Any]:
        raise RuntimeError("Echec synthetique controle")

    server_module.build_demo_payload = broken_demo
    try:
        with local_server() as base:
            status, payload = get_json(base + "/api/employee-case/demo?scenario=overtime-complete")
    finally:
        server_module.build_demo_payload = previous
    assert status == 500
    assert payload == {"ok": False, "error": "Echec synthetique controle"}


def test_frontend_loads_and_changes_scenarios() -> None:
    source = app_source("app.js")
    assert 'fetchJson("/api/employee-case/scenarios")' in source
    assert "/api/employee-case/demo?scenario=" in source
    assert 'caseScenarioSelect.addEventListener("change", loadEmployeeCase)' in source


def test_frontend_uses_backend_pipeline_statuses_and_two_views() -> None:
    source = app_source("app.js")
    html = app_source("index.html")
    assert "renderPipeline(payload.pipeline?.steps)" in source
    assert "currentCasePayload.employee_view" in source
    assert "currentCasePayload.expert_view" in source
    assert 'id="employeeViewButton"' in html and 'id="expertViewButton"' in html


def test_frontend_renders_blocked_contradictions_and_unavailable_experts() -> None:
    source = app_source("app.js")
    assert 'blocked: "Bloquee"' in source
    assert 'unavailable: "Indisponible"' in source
    assert "payload.contradictions" in source
    assert "sections.payroll_expert_summary" in source


def test_frontend_has_explicit_network_and_invalid_json_errors() -> None:
    source = app_source("app.js")
    assert "Reponse JSON invalide du serveur local." in source
    assert "Chargement impossible" in source
    assert "Liste des scenarios indisponible" in source


def test_frontend_uses_text_content_and_has_no_business_logic_duplication() -> None:
    source = app_source("app.js")
    assert "caseReportView.innerHTML" not in source
    assert "textContent" in source
    assert "DOCUMENT_REQUIREMENTS" not in source
    assert "CONFIDENCE_ORDER" not in source
    assert "score_percent" not in source
    assert "payroll-parameters" not in source
    assert "localStorage" not in source and "sessionStorage" not in source


def test_cockpit_controls_are_keyboard_accessible_and_status_not_color_only() -> None:
    html = app_source("index.html")
    styles = app_source("styles.css")
    assert '<button class="primary-button" type="button" id="loadCaseButton">' in html
    assert 'role="group" aria-label="Choisir la vue du rapport"' in html
    assert ".pipeline-steps li[data-status=\"completed\"]::before" in styles
    assert 'content: "OK"' in styles and 'content: "X"' in styles


def run_all() -> None:
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print(f"OK {name}")


if __name__ == "__main__":
    run_all()
