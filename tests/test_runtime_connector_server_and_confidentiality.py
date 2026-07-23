from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"


def load_server():
    sys.path.insert(0, str(SERVER_PATH.parent))
    spec = importlib.util.spec_from_file_location("nexus_runtime_lot2_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def answer():
    return {
        "query": "Question juridique synthétique",
        "confidence": "moyen",
        "route": {
            "main_domain": "temps_travail",
            "domains": ["temps_travail"],
            "engines": ["legifrance_code_travail"],
        },
        "sources": [{
            "origin": "legifrance_code_travail",
            "official_id": "LEGI-SYNTHETIC",
            "document": "Article synthétique",
            "source_layer": "code_travail",
        }],
    }


def expert_payload():
    legal = {
        "active": True,
        "ce_qui_est_certain": ["Constat synthétique."],
        "strategie_action_ordonnee": ["Contrôle humain."],
        "limites": [],
    }
    payroll = {"active": False}
    return {
        "expert_juriste": legal,
        "expert_paie": payroll,
        "experts": {"juriste": legal, "paie": payroll},
        "orchestration": {"reponse_synthetique_nexus": "Historique."},
    }


def configure(server, monkeypatch):
    monkeypatch.setattr(server, "run_router", lambda *_args, **_kwargs: answer())
    monkeypatch.setattr(server.orchestrator, "orchestrate", lambda _answer: expert_payload())
    monkeypatch.setattr(server.report_generator, "build_report", lambda _payload: {
        "sections": [{"id": "legacy", "title": "Historique", "items": ["Conservé"]}],
        "markdown": "legacy",
    })


def test_real_server_path_uses_connector_adapter_when_both_flags_are_enabled(monkeypatch):
    server = load_server()
    configure(server, monkeypatch)
    monkeypatch.setenv("NEXUS_CORE_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("NEXUS_CONNECTOR_RUNTIME_ENABLED", "true")
    payload = server.analyze_question("Question juridique synthétique")
    diagnostics = payload["runtime_integration"]["diagnostics"]
    assert payload["runtime_integration"]["runtime_mode"] == "core_v3"
    assert diagnostics["connector_adapter_called"] is True
    assert diagnostics["connector_count"] == 1
    assert diagnostics["connector_evidence_count"] == 1
    assert payload["analysis_report"]["sections"][0]["id"] == "legacy"


def test_connector_feature_disabled_preserves_lot1_behavior(monkeypatch):
    server = load_server()
    configure(server, monkeypatch)
    monkeypatch.setenv("NEXUS_CORE_RUNTIME_ENABLED", "true")
    monkeypatch.delenv("NEXUS_CONNECTOR_RUNTIME_ENABLED", raising=False)
    payload = server.analyze_question("Question juridique synthétique")
    diagnostics = payload["runtime_integration"]["diagnostics"]
    assert diagnostics["connector_runtime_enabled"] is False
    assert diagnostics["connector_adapter_called"] is False
    assert diagnostics["connector_count"] == 0


def test_connector_diagnostics_do_not_expose_source_or_personal_values(monkeypatch):
    server = load_server()
    configure(server, monkeypatch)
    sensitive = (
        "Personne Exemple", "299019999999999", "FR7630006000011234567890189",
        "private@example.invalid", "+33 6 00 00 00 00", "MATRICULE-PRIVATE",
    )
    value = answer()
    value["query"] = " ".join(sensitive)
    value["sources"][0]["excerpt"] = " ".join(sensitive)
    monkeypatch.setattr(server, "run_router", lambda *_args, **_kwargs: value)
    monkeypatch.setenv("NEXUS_CORE_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("NEXUS_CONNECTOR_RUNTIME_ENABLED", "true")
    payload = server.analyze_question(value["query"])
    diagnostics = json.dumps(payload["runtime_integration"]["diagnostics"], ensure_ascii=False)
    for item in sensitive:
        assert item not in diagnostics
    assert "Traceback" not in diagnostics
