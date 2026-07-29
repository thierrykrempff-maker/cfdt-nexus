from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from NEXUS_RUNTIME_INTEGRATION import sanitize_public_payload


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "nexus-local-interface"
RELEASE = (
    ROOT
    / "tests"
    / "fixtures"
    / "real_business_cases"
    / "v1_release_validation"
)


def _server_module():
    path = APP / "server.py"
    sys.path.insert(0, str(APP))
    spec = importlib.util.spec_from_file_location("nexus_release_security_server", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _answer(event: str) -> dict:
    return {
        "ok": True,
        "answer": {
            "query": event,
            "case_factual_core": {
                "primary_event": event,
                "requested_path": "QUESTION_SALARIE",
                "primary_grievance_or_decision": event,
                "facts_certain": [event],
            },
            "route": {
                "employee_path": "QUESTION_SALARIE",
                "domains": ["contrat_travail"],
                "analysis_suspended": False,
            },
            "short_answer": event,
            "working_position": "Vérifier les documents applicables.",
        },
    }


def test_public_responses_are_isolated_and_inputs_are_not_mutated() -> None:
    first_input = _answer("Situation synthétique A")
    second_input = _answer("Situation synthétique B")
    first = sanitize_public_payload(first_input)
    second = sanitize_public_payload(second_input)
    assert "Situation synthétique A" in " ".join(first["public_summary"]["situation"])
    assert "Situation synthétique B" not in json.dumps(first, ensure_ascii=False)
    assert "Situation synthétique B" in " ".join(second["public_summary"]["situation"])
    assert "public_summary" not in first_input["answer"]


def test_internal_http_error_never_exposes_exception_details() -> None:
    module = _server_module()
    handler = object.__new__(module.NexusHandler)
    logged = []
    sent = []
    handler.log_error = lambda message, *args: logged.append((message, args))
    handler.send_json = lambda status, payload: sent.append((status, payload))
    handler.send_internal_error(RuntimeError(r"secret C:\Users\Example\case.json"))
    serialized = json.dumps({"logged": logged, "sent": sent}, default=str)
    assert "secret" not in serialized
    assert "C:\\Users" not in serialized
    assert sent[0][1]["error"] == module.INTERNAL_ERROR_MESSAGE


def test_release_captures_contain_no_local_paths_or_runtime_diagnostics() -> None:
    forbidden = ("C:\\Users\\", "/home/", "/Users/", "/tmp/", "client_secret", "access_token")
    for path in RELEASE.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert not any(marker in text for marker in forbidden), path
        if path.name.endswith(".response.json"):
            payload = json.loads(text)["response"]
            assert "diagnostics" not in json.dumps(
                payload.get("analysis_report", {}), ensure_ascii=False
            ).casefold()


def test_interface_has_no_automatic_browser_storage() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    assert "localStorage" not in source
    assert "sessionStorage" not in source
