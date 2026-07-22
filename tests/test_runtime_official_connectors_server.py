from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from test_runtime_official_connectors import answer


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"


def load_server():
    sys.path.insert(0, str(SERVER_PATH.parent))
    spec = importlib.util.spec_from_file_location("nexus_runtime_lot6_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def configure(server, monkeypatch, value=None):
    monkeypatch.setattr(server, "run_router", lambda *_args, **_kwargs: value or answer())
    legal = {"active": True, "ce_qui_est_certain": ["Constat synthétique."], "limites": []}
    payroll = {"active": False}
    monkeypatch.setattr(server.orchestrator, "orchestrate", lambda _answer: {
        "expert_juriste": legal, "expert_paie": payroll,
        "experts": {"juriste": legal, "paie": payroll}, "orchestration": {},
    })
    monkeypatch.setattr(server.report_generator, "build_report", lambda _payload: {
        "sections": [{"id": "legacy", "items": ["Conservé"]}], "markdown": "legacy",
    })


def test_server_calls_official_connectors_and_core_when_flags_are_enabled(monkeypatch):
    server = load_server()
    configure(server, monkeypatch)
    monkeypatch.setenv("NEXUS_OFFICIAL_CONNECTORS_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("NEXUS_CORE_RUNTIME_ENABLED", "true")
    payload = server.analyze_question(answer()["query"])
    official = payload["official_connectors_runtime"]["diagnostics"]
    core = payload["runtime_integration"]["diagnostics"]
    assert official["connector_runtime_called"] is True
    assert official["connectors_used"] == ["cnil", "dreets_grand_est", "inrs"]
    assert core["connector_adapter_called"] is True
    assert core["connector_count"] == 3
    assert core["core_pipeline_called"] is True
    assert core["common_orchestrator_called"] is True


def test_server_feature_disabled_preserves_previous_report(monkeypatch):
    server = load_server()
    configure(server, monkeypatch)
    monkeypatch.delenv("NEXUS_OFFICIAL_CONNECTORS_RUNTIME_ENABLED", raising=False)
    monkeypatch.delenv("NEXUS_CORE_RUNTIME_ENABLED", raising=False)
    payload = server.analyze_question(answer()["query"])
    assert payload["official_connectors_runtime"]["diagnostics"] == {
        "connector_runtime_called": False,
        "connector_runtime_ms": 0,
        "connectors_used": [],
        "connector_runtime_fallback": None,
    }
    assert payload["analysis_report"]["sections"] == [{"id": "legacy", "items": ["Conservé"]}]


def test_connector_failure_preserves_the_previous_runtime_report(monkeypatch):
    server = load_server()
    malformed = answer()
    malformed["sources"][0]["url"] = "https://not-cnil.invalid/private"
    configure(server, monkeypatch, malformed)
    monkeypatch.setenv("NEXUS_CORE_RUNTIME_ENABLED", "true")
    monkeypatch.delenv("NEXUS_OFFICIAL_CONNECTORS_RUNTIME_ENABLED", raising=False)
    previous = server.analyze_question(malformed["query"])["analysis_report"]
    monkeypatch.setenv("NEXUS_OFFICIAL_CONNECTORS_RUNTIME_ENABLED", "true")
    failed = server.analyze_question(malformed["query"])
    assert failed["official_connectors_runtime"]["diagnostics"][
        "connector_runtime_fallback"
    ] == "OFFICIAL_CONNECTOR_RUNTIME_FAILED"
    assert failed["analysis_report"] == previous
