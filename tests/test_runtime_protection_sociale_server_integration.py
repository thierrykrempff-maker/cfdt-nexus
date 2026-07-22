from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from test_runtime_protection_sociale_search import write_chunks


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"


def load_server():
    sys.path.insert(0, str(SERVER_PATH.parent))
    spec = importlib.util.spec_from_file_location("nexus_runtime_lot5_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def answer():
    return {
        "query": "Que couvre la mutuelle pour l'optique ?",
        "confidence": "moyen",
        "route": {"main_domain": "juridique", "domains": ["juridique"], "intents": []},
        "sources": [],
    }


def experts():
    legal = {"active": True, "ce_qui_est_certain": ["Constat synthétique."], "limites": []}
    payroll = {"active": False}
    return {
        "expert_juriste": legal, "expert_paie": payroll,
        "experts": {"juriste": legal, "paie": payroll}, "orchestration": {},
    }


def configure(server, monkeypatch):
    monkeypatch.setattr(server, "run_router", lambda *_args, **_kwargs: answer())
    monkeypatch.setattr(server.orchestrator, "orchestrate", lambda _answer: experts())
    monkeypatch.setattr(server.report_generator, "build_report", lambda _payload: {
        "sections": [{"id": "legacy", "items": ["Conservé"]}],
        "sources": ["historical"], "markdown": "legacy",
    })


def test_real_server_path_enriches_report_from_read_only_metadata(tmp_path, monkeypatch):
    write_chunks(tmp_path)
    server = load_server()
    configure(server, monkeypatch)
    monkeypatch.setenv("NEXUS_PROTECTION_SOCIALE_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("NEXUS_PROTECTION_SOCIALE_PROCESSED_ROOT", str(tmp_path))
    payload = server.analyze_question(answer()["query"])
    diagnostics = payload["protection_sociale_runtime"]["diagnostics"]
    assert payload["protection_sociale_runtime"]["runtime_mode"] == "succeeded"
    assert diagnostics["protection_sociale_called"] is True
    assert diagnostics["protection_sociale_elements_used"] == 2
    assert payload["analysis_report"]["sections"][0]["id"] == "legacy"
    assert payload["analysis_report"]["sections"][-1]["id"] == "protection_sociale_runtime"
    assert payload["analysis_report"]["sources"] == ["historical"]


def test_feature_is_disabled_by_default_and_legacy_report_is_unchanged(monkeypatch):
    server = load_server()
    configure(server, monkeypatch)
    monkeypatch.delenv("NEXUS_PROTECTION_SOCIALE_RUNTIME_ENABLED", raising=False)
    payload = server.analyze_question(answer()["query"])
    assert payload["protection_sociale_runtime"]["runtime_mode"] == "disabled"
    assert payload["analysis_report"]["sections"] == [{"id": "legacy", "items": ["Conservé"]}]
    assert payload["analysis_report"]["sources"] == ["historical"]
