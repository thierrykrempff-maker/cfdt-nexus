from __future__ import annotations

from datetime import datetime, timezone

import NEXUS_RUNTIME_INTEGRATION.protection_sociale_runtime as runtime_module
from NEXUS_RUNTIME_INTEGRATION import RuntimeProtectionSocialeConfig
from NEXUS_RUNTIME_INTEGRATION.protection_sociale_runtime import (
    RuntimeProtectionSocialeIntegration,
    RuntimeProtectionSocialeMode,
    needs_protection_sociale,
)
from NEXUS_RUNTIME_INTEGRATION.protection_sociale_search import (
    ProtectionSocialeMetadataDocument,
    ProtectionSocialeSearchResult,
)


NOW = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)


def answer(query="Que prévoit la mutuelle pour l'optique ?"):
    return {
        "query": query,
        "route": {"main_domain": "juridique", "domains": ["juridique"], "intents": []},
    }


def search_result():
    document = ProtectionSocialeMetadataDocument(
        "synthetic-document", "notice", "mutuelle", "optique", "a" * 64
    )
    return ProtectionSocialeSearchResult((document,), 1, 2, 3)


class Gateway:
    def __init__(self, result=None, error=None):
        self.result = result or search_result()
        self.error = error
        self.calls = 0

    def search(self, _answer):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


def integration(gateway, enabled=True):
    ticks = iter((10.0, 10.004))
    return RuntimeProtectionSocialeIntegration(
        RuntimeProtectionSocialeConfig(enabled), gateway=gateway,
        clock=lambda: NOW, timer=lambda: next(ticks),
    )


def test_detection_is_bounded_and_avoids_payroll_and_retirement_false_positives():
    for query in (
        "mutuelle optique", "notice de prévoyance", "incapacité et invalidité",
        "tableau de garanties dentaires", "maintien de salaire",
    ):
        assert needs_protection_sociale(answer(query)) is True
    assert needs_protection_sociale(answer("Quel âge pour une retraite anticipée ?")) is False
    assert needs_protection_sociale(answer("Remboursement de mes frais professionnels")) is False
    routed = answer("Question générique")
    routed["route"]["domains"] = ["protection_sociale"]
    assert needs_protection_sociale(routed) is True


def test_feature_flag_disabled_and_irrelevant_question_do_not_call_gateway():
    gateway = Gateway()
    assert integration(gateway, False).integrate(answer()).mode is RuntimeProtectionSocialeMode.DISABLED
    assert integration(gateway).integrate(answer("Question de paie")).mode is RuntimeProtectionSocialeMode.NOT_NEEDED
    assert gateway.calls == 0


def test_real_adapter_pipeline_and_common_orchestrator_are_called(monkeypatch):
    calls = {"adapter": 0, "pipeline": 0, "common": 0}
    real_adapter = runtime_module.GenericConnectorAdapter
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

    monkeypatch.setattr(runtime_module, "GenericConnectorAdapter", TrackedAdapter)
    monkeypatch.setattr(runtime_module, "PipelineExecutor", TrackedPipeline)
    monkeypatch.setattr(runtime_module, "CommonExpertOrchestrator", TrackedCommon)
    result = integration(Gateway()).integrate(answer())
    assert result.mode is RuntimeProtectionSocialeMode.SUCCEEDED
    assert calls == {"adapter": 1, "pipeline": 1, "common": 1}
    assert result.diagnostics.protection_sociale_called is True
    assert result.diagnostics.protection_sociale_runtime_ms == 4
    assert result.diagnostics.protection_sociale_elements_used == 2
    assert result.document_count == 1
    assert result.chunk_count == 2


def test_unavailable_and_empty_results_fall_back_with_stable_codes():
    failed = integration(Gateway(error=RuntimeError("private path and raw content"))).integrate(answer())
    empty = integration(Gateway(ProtectionSocialeSearchResult(
        fallback_code="PROTECTION_SOCIALE_NO_RESULT"
    ))).integrate(answer())
    assert failed.diagnostics.protection_sociale_fallback == "PROTECTION_SOCIALE_UNAVAILABLE"
    assert empty.diagnostics.protection_sociale_fallback == "PROTECTION_SOCIALE_NO_RESULT"


def test_adapter_and_core_errors_use_fail_safe_diagnostics(monkeypatch):
    real_adapter = runtime_module.GenericConnectorAdapter

    class BrokenAdapter:
        def __init__(self, _source):
            pass

        def adapt(self):
            raise RuntimeError("private guarantee")

    monkeypatch.setattr(runtime_module, "GenericConnectorAdapter", BrokenAdapter)
    adapted = integration(Gateway()).integrate(answer())
    assert adapted.diagnostics.protection_sociale_fallback == "PROTECTION_SOCIALE_ADAPTER_FAILED"

    monkeypatch.setattr(runtime_module, "GenericConnectorAdapter", real_adapter)

    class BrokenPipeline:
        def execute(self, *_args, **_kwargs):
            raise RuntimeError("private identifier")

    monkeypatch.setattr(runtime_module, "PipelineExecutor", BrokenPipeline)
    core = integration(Gateway()).integrate(answer())
    assert core.diagnostics.protection_sociale_fallback == "PROTECTION_SOCIALE_CORE_FAILED"


def test_feature_flag_is_independent_from_other_runtime_flags():
    config = RuntimeProtectionSocialeConfig.from_env({
        "NEXUS_CORE_RUNTIME_ENABLED": "true",
        "NEXUS_CSE_MEMORY_RUNTIME_ENABLED": "true",
        "NEXUS_RETIREMENT_RUNTIME_ENABLED": "true",
    })
    assert config.enabled is False
    enabled = RuntimeProtectionSocialeConfig.from_env({
        "NEXUS_PROTECTION_SOCIALE_RUNTIME_ENABLED": "true",
        "NEXUS_CORE_RUNTIME_ENABLED": "false",
    })
    assert enabled.enabled is True
