from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"


def load_server():
    sys.path.insert(0, str(SERVER_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "nexus_runtime_syndical_r0_server", SERVER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def answer():
    return {
        "query": "L'employeur peut-il modifier mes horaires et comment réagir avec le CSE ?",
        "confidence": "moyen",
        "route": {
            "main_domain": "temps_travail",
            "domains": ["temps_travail", "cse"],
            "intents": ["conseiller_salarie"],
        },
        "sources": [],
    }


def experts():
    legal = {"active": True, "ce_qui_est_certain": [], "limites": []}
    payroll = {"active": False}
    return {
        "expert_juriste": legal,
        "expert_paie": payroll,
        "experts": {"juriste": legal, "paie": payroll},
        "orchestration": {},
    }


def configure(server, monkeypatch):
    monkeypatch.setattr(server, "run_router", lambda *_args, **_kwargs: answer())
    monkeypatch.setattr(server.orchestrator, "orchestrate", lambda _answer: experts())
    monkeypatch.setattr(
        server.report_generator,
        "build_report",
        lambda _payload: {
            "sections": [{"id": "legacy", "items": ["Conservé"]}],
            "markdown": "legacy",
        },
    )


def test_server_calls_syndical_runtime_when_explicitly_enabled(monkeypatch):
    server = load_server()
    configure(server, monkeypatch)
    monkeypatch.setenv("NEXUS_SYNDICAL_REASONING_RUNTIME_ENABLED", "true")
    payload = server.analyze_question(answer()["query"])
    assert payload["syndical_reasoning_runtime"]["mode"] == "SUCCEEDED"
    assert payload["syndical_reasoning_runtime"]["diagnostics"]["called"] is True
    assert [item["id"] for item in payload["analysis_report"]["sections"]] == [
        "legacy",
        "syndical_reasoning_runtime",
    ]


def test_server_preserves_historical_report_when_flag_is_absent(monkeypatch):
    server = load_server()
    configure(server, monkeypatch)
    monkeypatch.delenv("NEXUS_SYNDICAL_REASONING_RUNTIME_ENABLED", raising=False)
    payload = server.analyze_question(answer()["query"])
    assert payload["syndical_reasoning_runtime"]["mode"] == "DISABLED"
    assert payload["analysis_report"] == {
        "sections": [{"id": "legacy", "items": ["Conservé"]}],
        "markdown": "legacy",
    }
