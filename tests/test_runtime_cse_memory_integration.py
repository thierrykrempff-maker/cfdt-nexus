from __future__ import annotations

from datetime import datetime, timezone

import NEXUS_RUNTIME_INTEGRATION.cse_memory_runtime as runtime_module
from NEXUS_RUNTIME_INTEGRATION import RuntimeCSEMemoryConfig
from NEXUS_RUNTIME_INTEGRATION.cse_memory_runtime import (
    RuntimeCSEMemoryIntegration, RuntimeCSEMemoryMode,
)
from NEXUS_RUNTIME_INTEGRATION.cse_memory_search import CSEMemorySearchResult
from automation.cse_memory.document_models import DocumentRecord


NOW = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)


def answer(query="Retrouve le PV CSE sur la réorganisation"):
    return {
        "query": query,
        "route": {"main_domain": "cse", "domains": ["cse"], "intents": []},
    }


def document():
    return DocumentRecord(
        "INTERNAL-DOCUMENT", "private/internal.pdf", "internal.pdf", ".pdf", 100,
        "a" * 64, NOW.isoformat(), "2025", "pv", "existing", "prepared_chunk_lookup",
        "extracted", None, None, "", 100, None, None, None, None, {}, [], NOW.isoformat(),
    )


class Gateway:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def search(self, _answer):
        self.calls += 1
        return self.result


def integration(gateway, enabled=True):
    return RuntimeCSEMemoryIntegration(
        RuntimeCSEMemoryConfig(enabled), gateway=gateway, clock=lambda: NOW
    )


def test_feature_flag_disabled_does_not_call_memory():
    gateway = Gateway(CSEMemorySearchResult((document(),), 1, 1, 2))
    result = integration(gateway, False).integrate(answer())
    assert result.mode is RuntimeCSEMemoryMode.DISABLED
    assert gateway.calls == 0


def test_irrelevant_question_does_not_call_memory():
    gateway = Gateway(CSEMemorySearchResult((document(),), 1, 1, 2))
    value = answer("Comment vérifier ma fiche de paie ?")
    value["route"]["domains"] = ["paie_remuneration"]
    result = integration(gateway).integrate(value)
    assert result.mode is RuntimeCSEMemoryMode.NOT_NEEDED
    assert gateway.calls == 0


def test_real_cse_adapter_core_and_common_orchestrator_are_called(monkeypatch):
    calls = {"adapter": 0, "core": 0, "common": 0}
    gateway = Gateway(CSEMemorySearchResult((document(),), 1, 2, 3))
    real_adapter = runtime_module.CSEAdapter
    real_pipeline = runtime_module.PipelineExecutor
    real_common = runtime_module.CommonExpertOrchestrator

    class TrackedAdapter(real_adapter):
        def adapt(self):
            calls["adapter"] += 1
            return super().adapt()

    class TrackedPipeline(real_pipeline):
        def execute(self, *args, **kwargs):
            calls["core"] += 1
            return super().execute(*args, **kwargs)

    class TrackedCommon(real_common):
        def execute(self, request):
            calls["common"] += 1
            return super().execute(request)

    monkeypatch.setattr(runtime_module, "CSEAdapter", TrackedAdapter)
    monkeypatch.setattr(runtime_module, "PipelineExecutor", TrackedPipeline)
    monkeypatch.setattr(runtime_module, "CommonExpertOrchestrator", TrackedCommon)
    result = integration(gateway).integrate(answer())
    assert result.mode is RuntimeCSEMemoryMode.SUCCEEDED
    assert calls["adapter"] >= 2  # explicit adaptation plus Core engine execution
    assert calls["core"] == 1
    assert calls["common"] == 1
    assert result.diagnostics.document_count == 1
    assert result.diagnostics.chunk_count == 2
    assert result.diagnostics.adapter_called is True
    assert result.diagnostics.core_pipeline_called is True
    assert result.diagnostics.common_orchestrator_called is True


def test_empty_search_and_search_error_use_safe_fallback():
    empty = integration(Gateway(CSEMemorySearchResult(fallback_code="CSE_MEMORY_NO_MATCH"))).integrate(answer())
    assert empty.mode is RuntimeCSEMemoryMode.FALLBACK
    assert empty.diagnostics.fallback_code == "CSE_MEMORY_NO_MATCH"

    class BrokenGateway:
        def search(self, _answer):
            raise RuntimeError("PRIVATE PATH C:/private/document.pdf")

    failed = integration(BrokenGateway()).integrate(answer())
    assert failed.mode is RuntimeCSEMemoryMode.FALLBACK
    assert failed.diagnostics.fallback_code == "CSE_MEMORY_SEARCH_FAILED"
