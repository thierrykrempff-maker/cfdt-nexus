from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

from NEXUS_RUNTIME_INTEGRATION.cse_memory_runtime import (
    RuntimeCSEMemoryDiagnostics, RuntimeCSEMemoryMode, RuntimeCSEMemoryResult,
)
from NEXUS_RUNTIME_INTEGRATION.report_mapper import RuntimeCSEMemoryReportMapper

from test_runtime_cse_memory_search import write_chunks


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"


def load_server():
    sys.path.insert(0, str(SERVER_PATH.parent))
    spec = importlib.util.spec_from_file_location("nexus_runtime_lot3_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def answer():
    return {
        "query": "Que disait l'ancien PV CSE sur la réorganisation ?",
        "confidence": "moyen",
        "route": {"main_domain": "cse", "domains": ["cse"], "intents": []},
        "sources": [],
    }


def experts():
    legal = {"active": True, "ce_qui_est_certain": ["Constat synthétique."], "limites": []}
    payroll = {"active": False}
    return {
        "expert_juriste": legal, "expert_paie": payroll,
        "experts": {"juriste": legal, "paie": payroll}, "orchestration": {},
    }


def test_real_server_path_adds_bounded_cse_section(tmp_path, monkeypatch):
    write_chunks(tmp_path)
    server = load_server()
    monkeypatch.setattr(server, "run_router", lambda *_args, **_kwargs: answer())
    monkeypatch.setattr(server.orchestrator, "orchestrate", lambda _answer: experts())
    monkeypatch.setattr(server.report_generator, "build_report", lambda _payload: {
        "sections": [{"id": "legacy", "title": "Historique", "items": ["Conservé"]}],
        "markdown": "legacy",
    })
    monkeypatch.setenv("NEXUS_CSE_MEMORY_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("NEXUS_CSE_MEMORY_PROCESSED_ROOT", str(tmp_path))
    payload = server.analyze_question(answer()["query"])
    diagnostics = payload["cse_memory_runtime"]["diagnostics"]
    assert payload["cse_memory_runtime"]["runtime_mode"] == "succeeded"
    assert diagnostics["called"] is True
    assert diagnostics["document_count"] == 1
    assert payload["analysis_report"]["sections"][0]["id"] == "legacy"
    assert payload["analysis_report"]["sections"][-1]["id"] == "cse_memory_runtime"


def test_fallback_returns_exact_prior_report_and_diagnostics_are_confidential():
    report = {"sections": [{"id": "legacy"}], "markdown": "unchanged"}
    diagnostics = RuntimeCSEMemoryDiagnostics(
        True, True, duration_ms=4, fallback_triggered=True,
        fallback_code="CSE_MEMORY_SEARCH_FAILED",
    )
    result = RuntimeCSEMemoryResult(RuntimeCSEMemoryMode.FALLBACK, diagnostics)
    assert RuntimeCSEMemoryReportMapper().map(report, result) is report
    serialized = json.dumps(result.to_dict(), ensure_ascii=False)
    for forbidden in (
        "C:/private/document.pdf", "INTERNAL-DOCUMENT", "INTERNAL-CHUNK",
        "Personne Exemple", "299019999999999", "FR7630006000011234567890189",
    ):
        assert forbidden not in serialized


def test_server_converts_unexpected_cse_runtime_failure_to_fallback(monkeypatch):
    server = load_server()
    monkeypatch.setattr(server, "run_router", lambda *_args, **_kwargs: answer())
    monkeypatch.setattr(server.orchestrator, "orchestrate", lambda _answer: experts())
    monkeypatch.setattr(server.report_generator, "build_report", lambda _payload: {
        "sections": [{"id": "legacy"}], "markdown": "unchanged",
    })
    monkeypatch.setenv("NEXUS_CSE_MEMORY_RUNTIME_ENABLED", "true")
    monkeypatch.setattr(
        server.RuntimeCSEMemoryIntegration,
        "integrate",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("synthetic")),
    )
    payload = server.analyze_question(answer()["query"])
    cse = payload["cse_memory_runtime"]
    assert cse["runtime_mode"] == "fallback"
    assert cse["diagnostics"]["called"] is True
    assert cse["diagnostics"]["fallback_code"] == "CSE_MEMORY_RUNTIME_FAILED"
    assert payload["analysis_report"]["markdown"] == "unchanged"


def test_success_report_exposes_counts_but_no_raw_document():
    report = {"sections": [], "markdown": "legacy"}
    result = RuntimeCSEMemoryResult(
        RuntimeCSEMemoryMode.SUCCEEDED,
        RuntimeCSEMemoryDiagnostics(True, True, 1, 2, 3, True, True, True),
        ("CSE Memory : 1 document(s) rapproché(s).",),
    )
    mapped = RuntimeCSEMemoryReportMapper().map(report, result)
    serialized = json.dumps(mapped, ensure_ascii=False)
    assert "1 document" in serialized
    assert "INTERNAL-DOCUMENT" not in serialized
    assert "confidential/internal-name.pdf" not in serialized
