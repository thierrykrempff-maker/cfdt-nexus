from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import threading
import urllib.request

import pytest


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"


def _server_module():
    sys.path.insert(0, str(SERVER_PATH.parent))
    spec = importlib.util.spec_from_file_location("controlled_validation_server", SERVER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _answer(query: str) -> dict[str, object]:
    return {
        "query": query,
        "route": {"domains": ["disciplinaire"]},
        "sources": [{"document": "Code du travail synthétique"}],
        "facts": [{"statement": "Fait synthétique", "documented": False}],
    }


def test_disabled_flag_keeps_historical_report_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    server = _server_module()
    monkeypatch.setattr(server, "run_router", lambda query, limit=6: _answer(query))
    monkeypatch.delenv("NEXUS_FINAL_ASSISTANT_RUNTIME_ENABLED", raising=False)
    payload = server.analyze_question("Une sanction disciplinaire est évoquée.")
    assert payload["final_assistant_runtime"]["mode"] == "DISABLED"
    assert payload["final_assistant_runtime"]["assistant"] is None


def test_enabled_flag_exposes_bounded_final_assistant(monkeypatch: pytest.MonkeyPatch) -> None:
    server = _server_module()
    monkeypatch.setattr(server, "run_router", lambda query, limit=6: _answer(query))
    monkeypatch.setenv("NEXUS_FINAL_ASSISTANT_RUNTIME_ENABLED", "true")
    monkeypatch.delenv("NEXUS_EXPERT_PAIE_V2_RUNTIME_ENABLED", raising=False)
    payload = server.analyze_question("Une sanction disciplinaire est évoquée.")
    assert payload["final_assistant_runtime"]["mode"] == "SUCCEEDED"
    assert "expert_paie_v2" not in payload["final_assistant_runtime"]["diagnostics"]["engines_used"]
    public = server.sanitize_public_payload(payload)
    assert "traceback" not in json.dumps(public, ensure_ascii=False).casefold()


def test_explicit_payroll_flag_is_bounded_to_payroll_question(monkeypatch: pytest.MonkeyPatch) -> None:
    server = _server_module()
    monkeypatch.setattr(
        server,
        "run_router",
        lambda query, limit=6: {
            **_answer(query),
            "route": {"domains": ["paie_remuneration"]},
            "payroll_rule_context": {"documents": ["bulletin synthétique"]},
        },
    )
    monkeypatch.setenv("NEXUS_FINAL_ASSISTANT_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("NEXUS_EXPERT_PAIE_V2_RUNTIME_ENABLED", "true")
    payload = server.analyze_public_question("Une rubrique de paie est à vérifier.")
    assert payload["final_assistant_runtime"]["mode"] in {"SUCCEEDED", "FALLBACK"}
    assert "c:\\" not in json.dumps(payload, ensure_ascii=False).casefold()


def test_local_http_endpoint_returns_public_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    server_module = _server_module()
    monkeypatch.setattr(
        server_module,
        "run_router",
        lambda query, limit=6: _answer(query),
    )
    monkeypatch.setenv("NEXUS_FINAL_ASSISTANT_RUNTIME_ENABLED", "true")
    httpd = server_module.ThreadingHTTPServer(("127.0.0.1", 0), server_module.NexusHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{httpd.server_address[1]}/api/analyze",
            data=json.dumps({"query": "Une sanction disciplinaire est évoquée."}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert response.status == 200
        assert payload["ok"] is True
        assert payload["final_assistant_runtime"]["mode"] == "SUCCEEDED"
    finally:
        httpd.shutdown()
        httpd.server_close()
