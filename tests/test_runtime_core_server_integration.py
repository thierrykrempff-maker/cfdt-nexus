from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"


def load_server():
    sys.path.insert(0, str(SERVER_PATH.parent))
    spec = importlib.util.spec_from_file_location("nexus_runtime_lot1_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def router_answer():
    return {
        "query": "Question Paie synthétique",
        "confidence": "moyen",
        "route": {"main_domain": "paie_remuneration", "domains": ["paie_remuneration"], "router_version": "1.2"},
        "sources": [],
    }


def expert_payload():
    legal = {"active": False, "name": "Juriste"}
    payroll = {
        "active": True,
        "name": "Expert Paie V0",
        "objet_du_controle": "Contrôle synthétique.",
        "elements_du_bulletin_concernes": [],
        "donnees_necessaires_au_calcul": [],
        "limites": [],
    }
    return {
        "expert_juriste": legal,
        "expert_paie": payroll,
        "experts": {"juriste": legal, "paie": payroll},
        "orchestration": {"reponse_synthetique_nexus": "Réponse historique."},
    }


def test_server_keeps_historical_report_when_core_disabled(monkeypatch):
    server = load_server()
    monkeypatch.delenv("NEXUS_CORE_RUNTIME_ENABLED", raising=False)
    monkeypatch.setattr(server, "run_router", lambda *_args, **_kwargs: router_answer())
    monkeypatch.setattr(server.orchestrator, "orchestrate", lambda _answer: expert_payload())
    historical = {"sections": [{"id": "legacy", "title": "Historique", "items": ["Conservé"]}], "markdown": "legacy"}
    monkeypatch.setattr(server.report_generator, "build_report", lambda _payload: historical)
    payload = server.analyze_question("Question Paie synthétique")
    assert payload["runtime_integration"]["runtime_mode"] == "legacy"
    assert payload["analysis_report"] is historical
    assert payload["expert_paie"] == expert_payload()["expert_paie"]


def test_server_real_path_calls_core_and_enriches_existing_report(monkeypatch):
    server = load_server()
    monkeypatch.setenv("NEXUS_CORE_RUNTIME_ENABLED", "true")
    monkeypatch.setattr(server, "run_router", lambda *_args, **_kwargs: router_answer())
    monkeypatch.setattr(server.orchestrator, "orchestrate", lambda _answer: expert_payload())
    monkeypatch.setattr(server.report_generator, "build_report", lambda _payload: {
        "sections": [{"id": "legacy", "title": "Historique", "items": ["Conservé"]}],
        "generated_from": ["legacy"],
        "markdown": "legacy",
    })
    payload = server.analyze_question("Question Paie synthétique")
    diagnostics = payload["runtime_integration"]["diagnostics"]
    assert payload["runtime_integration"]["runtime_mode"] == "core_v3"
    assert diagnostics["payroll_adapter_called"] is True
    assert diagnostics["core_pipeline_called"] is True
    assert diagnostics["common_orchestrator_called"] is True
    assert payload["analysis_report"]["sections"][0]["id"] == "legacy"
    assert payload["analysis_report"]["sections"][-1]["id"] == "core_v3_runtime"


def test_server_core_failure_preserves_historical_payload(monkeypatch):
    server = load_server()
    monkeypatch.setenv("NEXUS_CORE_RUNTIME_ENABLED", "true")
    monkeypatch.setattr(server, "run_router", lambda *_args, **_kwargs: router_answer())
    monkeypatch.setattr(server.orchestrator, "orchestrate", lambda _answer: expert_payload())
    historical = {"sections": [], "markdown": "legacy"}
    monkeypatch.setattr(server.report_generator, "build_report", lambda _payload: historical)
    monkeypatch.setattr(server.RuntimeCoreIntegration, "_run_core", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("synthetic")))
    payload = server.analyze_question("Question Paie synthétique")
    assert payload["runtime_integration"]["runtime_mode"] == "core_v3_fallback"
    diagnostics = payload["runtime_integration"]["diagnostics"]
    assert diagnostics["payroll_executed"] is True
    assert diagnostics["payroll_adapter_called"] is True
    assert diagnostics["core_pipeline_called"] is True
    assert payload["analysis_report"] is historical
    assert payload["expert_paie"] == expert_payload()["expert_paie"]
