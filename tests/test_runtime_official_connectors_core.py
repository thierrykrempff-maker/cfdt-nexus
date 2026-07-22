from __future__ import annotations

from datetime import datetime, timezone

import NEXUS_RUNTIME_INTEGRATION.integration as core_module
from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeCoreIntegration,
    RuntimeCoreIntegrationInput,
    RuntimeIntegrationConfig,
    RuntimeMode,
    RuntimeOfficialConnectorsConfig,
)
from NEXUS_RUNTIME_INTEGRATION.official_connectors_runtime import (
    RuntimeOfficialConnectorsIntegration,
)
from test_runtime_official_connectors import answer


NOW = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)


def test_official_snapshots_cross_adapter_pipeline_and_common_orchestrator(monkeypatch):
    official = RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(True), clock=lambda: NOW
    ).integrate(answer())
    calls = {"adapter": 0, "pipeline": 0, "common": 0}
    real_adapter = core_module.GenericConnectorAdapter
    real_pipeline = core_module.PipelineExecutor
    real_common = core_module.CommonExpertOrchestrator

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

    monkeypatch.setattr(core_module, "GenericConnectorAdapter", TrackedAdapter)
    monkeypatch.setattr(core_module, "PipelineExecutor", TrackedPipeline)
    monkeypatch.setattr(core_module, "CommonExpertOrchestrator", TrackedCommon)
    result = RuntimeCoreIntegration(RuntimeIntegrationConfig(True), clock=lambda: NOW).integrate(
        RuntimeCoreIntegrationInput(
            answer(),
            {"active": True, "ce_qui_est_certain": ["Constat synthétique."]},
            {"active": False},
            {},
            official.inputs,
            True,
        )
    )
    assert result.runtime_mode is RuntimeMode.CORE_V3
    assert calls == {"adapter": 3, "pipeline": 1, "common": 1}
    assert result.diagnostics.connector_count == 3
    assert result.diagnostics.connector_evidence_count == 3
    assert set(result.selected_experts) >= {
        "connector_cnil", "connector_dreets_grand_est", "connector_inrs"
    }


def test_official_failure_leaves_existing_core_inputs_untouched():
    malformed = answer()
    malformed["sources"][0]["url"] = "http://cnil.fr/interdit"
    official = RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(True), clock=lambda: NOW
    ).integrate(malformed)
    assert official.inputs == ()
    result = RuntimeCoreIntegration(RuntimeIntegrationConfig(True), clock=lambda: NOW).integrate(
        RuntimeCoreIntegrationInput(
            answer(),
            {"active": True, "ce_qui_est_certain": ["Historique conservé."]},
            {"active": False},
            {},
            official.inputs,
            True,
        )
    )
    assert result.runtime_mode is RuntimeMode.CORE_V3
    assert result.diagnostics.legal_executed is True
    assert result.diagnostics.connector_count == 0
