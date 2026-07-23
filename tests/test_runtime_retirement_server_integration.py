from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"


def load_server():
    sys.path.insert(0, str(SERVER_PATH.parent))
    spec = importlib.util.spec_from_file_location("nexus_runtime_lot4_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def answer():
    return {
        "query": "Quelles démarches pour vérifier ma carrière longue ?",
        "confidence": "moyen",
        "route": {"main_domain": "juridique", "domains": ["juridique"], "intents": []},
        "sources": [],
    }


def experts():
    legal = {"active": True, "ce_qui_est_certain": ["Constat synthétique."], "limites": []}
    payroll = {"active": False}
    return {
        "expert_juriste": legal,
        "expert_paie": payroll,
        "experts": {"juriste": legal, "paie": payroll},
        "orchestration": {},
    }


def test_real_server_path_calls_retirement_and_enriches_report(monkeypatch):
    server = load_server()
    monkeypatch.setattr(server, "run_router", lambda *_args, **_kwargs: answer())
    monkeypatch.setattr(server.orchestrator, "orchestrate", lambda _answer: experts())
    monkeypatch.setattr(server.report_generator, "build_report", lambda _payload: {
        "sections": [{"id": "legacy", "title": "Historique", "items": ["Conservé"]}],
        "markdown": "legacy",
    })
    monkeypatch.setenv("NEXUS_RETIREMENT_RUNTIME_ENABLED", "true")
    payload = server.analyze_question(answer()["query"])
    diagnostics = payload["retirement_runtime"]["diagnostics"]
    assert payload["retirement_runtime"]["runtime_mode"] == "succeeded"
    assert diagnostics["retirement_called"] is True
    assert diagnostics["retirement_elements_used"] == 2
    assert payload["analysis_report"]["sections"][0]["id"] == "legacy"
    assert payload["analysis_report"]["sections"][-1]["id"] == "retirement_runtime"


def test_retirement_feature_is_disabled_by_default(monkeypatch):
    server = load_server()
    monkeypatch.delenv("NEXUS_RETIREMENT_RUNTIME_ENABLED", raising=False)
    monkeypatch.setattr(server, "run_router", lambda *_args, **_kwargs: answer())
    monkeypatch.setattr(server.orchestrator, "orchestrate", lambda _answer: experts())
    legacy = {"sections": [{"id": "legacy"}], "markdown": "legacy"}
    monkeypatch.setattr(server.report_generator, "build_report", lambda _payload: legacy)
    payload = server.analyze_question(answer()["query"])
    assert payload["retirement_runtime"]["runtime_mode"] == "disabled"
    assert payload["analysis_report"] is legacy
