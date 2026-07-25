from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"


def load_server():
    sys.path.insert(0, str(SERVER_PATH.parent))
    spec = importlib.util.spec_from_file_location("nexus_ui1_server", SERVER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_historical_fallback_remains_default(monkeypatch) -> None:
    monkeypatch.delenv("NEXUS_FINAL_ASSISTANT_RUNTIME_ENABLED", raising=False)
    server = load_server()
    monkeypatch.setattr(server, "run_router", lambda query, source_limit=6: {
        "ok": True,
        "query": query,
        "confidence": "moyen",
        "short_answer": "Analyse historique.",
        "working_position": "À vérifier.",
        "route": {"domains": ["temps_travail"], "intents": [], "engines": []},
        "sources": [],
        "findings": [],
        "documents_to_request": [],
        "questions_to_ask": [],
        "warnings": [],
    })
    monkeypatch.setattr(server.orchestrator, "orchestrate", lambda answer: {
        "orchestration": {
            "question_posee": answer["query"],
            "niveau_de_confiance": "moyen",
            "domaines_detectes": ["temps_travail"],
            "experts_mobilises": [],
            "reponse_synthetique_nexus": "Analyse historique.",
            "position_de_travail": "À vérifier.",
            "documents_necessaires": [],
            "questions_utiles": [],
            "limites": [],
        },
        "expert_juriste": {"active": False},
        "expert_paie": {"active": False},
    })
    payload = server.analyze_question("Question UI1")
    assert payload["final_assistant_runtime"]["mode"] == "DISABLED"


def test_frontend_posts_to_existing_public_endpoint() -> None:
    js = (ROOT / "apps" / "nexus-local-interface" / "app.js").read_text(encoding="utf-8")
    assert 'fetch("/api/analyze"' in js
    assert "body: JSON.stringify(requestPayload)" in js
    assert "expert_paie_v2" not in js.split("allowed_engines:", 1)[1].split("}", 1)[0]
