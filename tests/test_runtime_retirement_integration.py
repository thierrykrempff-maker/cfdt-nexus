from __future__ import annotations

from datetime import datetime, timezone

import NEXUS_RUNTIME_INTEGRATION.retirement_runtime as runtime_module
from NEXUS_RUNTIME_INTEGRATION import RuntimeRetirementConfig
from NEXUS_RUNTIME_INTEGRATION.retirement_runtime import (
    RuntimeRetirementGateway,
    RuntimeRetirementIntegration,
    RuntimeRetirementMode,
    needs_retirement,
)


NOW = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)


def answer(query="Quels éléments vérifier pour ma retraite et ma carrière longue ?"):
    return {
        "query": query,
        "route": {"main_domain": "juridique", "domains": ["juridique"], "intents": []},
    }


def integration(*, enabled=True, gateway=None):
    ticks = iter((10.0, 10.004))
    return RuntimeRetirementIntegration(
        RuntimeRetirementConfig(enabled),
        gateway=gateway,
        clock=lambda: NOW,
        timer=lambda: next(ticks),
    )


def test_detection_reuses_route_and_closed_retirement_vocabulary():
    routed = answer("Question générique")
    routed["route"]["domains"] = ["retirement_penibility"]
    assert needs_retirement(routed) is True
    assert needs_retirement(answer("Comment vérifier mon bulletin de paie ?")) is False
    for query in ("âge légal", "départ anticipé", "C2P", "pénibilité", "trimestres"):
        assert needs_retirement(answer(query)) is True


def test_disabled_flag_and_irrelevant_question_do_not_call_retirement():
    class Gateway:
        def build(self, _request_id):
            raise AssertionError("gateway must not be called")

    assert integration(enabled=False, gateway=Gateway()).integrate(answer()).mode is RuntimeRetirementMode.DISABLED
    assert integration(gateway=Gateway()).integrate(answer("Question de paie")).mode is RuntimeRetirementMode.NOT_NEEDED


def test_real_retirement_adapter_pipeline_and_common_orchestrator_are_called(monkeypatch):
    calls = {"adapter": 0, "pipeline": 0, "common": 0}
    real_adapter = runtime_module.RetirementAdapter
    real_pipeline = runtime_module.PipelineExecutor
    real_common = runtime_module.CommonExpertOrchestrator

    class TrackedAdapter(real_adapter):
        def adapt(self):
            calls["adapter"] += 1
            return super().adapt()

    class TrackedPipeline(real_pipeline):
        def execute(self, *args, **kwargs):
            calls["pipeline"] += 1
            return super().execute(*args, **kwargs)

    class TrackedCommon(real_common):
        def execute(self, request):
            calls["common"] += 1
            return super().execute(request)

    monkeypatch.setattr(runtime_module, "RetirementAdapter", TrackedAdapter)
    monkeypatch.setattr(runtime_module, "PipelineExecutor", TrackedPipeline)
    monkeypatch.setattr(runtime_module, "CommonExpertOrchestrator", TrackedCommon)

    result = integration(gateway=RuntimeRetirementGateway()).integrate(answer())
    assert result.mode is RuntimeRetirementMode.SUCCEEDED
    assert calls == {"adapter": 2, "pipeline": 1, "common": 1}
    assert result.diagnostics.retirement_called is True
    assert result.diagnostics.retirement_runtime_ms == 4
    assert result.diagnostics.retirement_elements_used == 2
    assert result.diagnostics.retirement_fallback is None


def test_gateway_failure_empty_result_and_pipeline_failure_fall_back(monkeypatch):
    class BrokenGateway:
        def build(self, _request_id):
            raise RuntimeError("private value and private path")

    class EmptyGateway:
        def build(self, _request_id):
            return None

    failed = integration(gateway=BrokenGateway()).integrate(answer())
    empty = integration(gateway=EmptyGateway()).integrate(answer())
    assert failed.diagnostics.retirement_fallback == "RETIREMENT_RUNTIME_UNAVAILABLE"
    assert empty.diagnostics.retirement_fallback == "RETIREMENT_NO_RESULT"

    class BrokenPipeline:
        def execute(self, *_args, **_kwargs):
            raise RuntimeError("sensitive internal identifier")

    monkeypatch.setattr(runtime_module, "PipelineExecutor", BrokenPipeline)
    core = integration(gateway=RuntimeRetirementGateway()).integrate(answer())
    assert core.mode is RuntimeRetirementMode.FALLBACK
    assert core.diagnostics.retirement_fallback == "RETIREMENT_CORE_FAILED"
