from __future__ import annotations

from datetime import datetime, timezone

import NEXUS_RUNTIME_INTEGRATION.integration as integration_module
from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeConnectorConfig,
    RuntimeConnectorPayloadMapper,
    RuntimeCoreIntegration,
    RuntimeCoreIntegrationInput,
    RuntimeIntegrationConfig,
    RuntimeMode,
)


NOW = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)


def answer():
    return {
        "query": "Que prévoit le Code du travail ?",
        "confidence": "fort",
        "generated_at": NOW.isoformat(),
        "route": {
            "main_domain": "temps_travail",
            "domains": ["temps_travail"],
            "engines": ["legifrance_code_travail", "judilibre_jurisprudence", "pratique_officielle"],
        },
        "sources": [
            {"origin": "legifrance_code_travail", "official_id": "LEGI-1", "document": "Article synthétique", "source_layer": "code_travail"},
            {"origin": "judilibre_jurisprudence", "official_id": "JUDI-1", "document": "Décision synthétique", "source_layer": "jurisprudence"},
            {"origin": "cdtn_pratique_officielle", "official_id": "CDTN-1", "document": "Fiche synthétique", "source_layer": "pratique_officielle"},
        ],
    }


def legal():
    return {
        "active": True,
        "ce_qui_est_certain": ["Constat synthétique."],
        "strategie_action_ordonnee": ["Contrôle humain."],
        "limites": [],
    }


def source(mapping=None):
    mapped = mapping or RuntimeConnectorPayloadMapper(RuntimeConnectorConfig(True)).map(answer())
    return RuntimeCoreIntegrationInput(
        answer(), legal(), {"active": False}, {}, mapped.inputs, True, mapped.fallback_code
    )


def test_real_generic_connector_adapter_and_common_orchestrator_are_called(monkeypatch):
    calls = {"adapter": 0, "common": 0}
    real_adapter = integration_module.GenericConnectorAdapter
    real_common = integration_module.CommonExpertOrchestrator

    class TrackedAdapter(real_adapter):
        def adapt(self):
            calls["adapter"] += 1
            return super().adapt()

    class TrackedCommon(real_common):
        def execute(self, request):
            calls["common"] += 1
            return super().execute(request)

    monkeypatch.setattr(integration_module, "GenericConnectorAdapter", TrackedAdapter)
    monkeypatch.setattr(integration_module, "CommonExpertOrchestrator", TrackedCommon)
    result = RuntimeCoreIntegration(RuntimeIntegrationConfig(True), clock=lambda: NOW).integrate(source())
    assert result.runtime_mode is RuntimeMode.CORE_V3
    assert calls == {"adapter": 3, "common": 1}
    assert result.diagnostics.connector_adapter_called is True
    assert result.diagnostics.connector_count == 3
    assert result.diagnostics.connector_snapshot_count == 3
    assert result.diagnostics.connector_evidence_count == 3
    assert set(result.selected_experts) >= {
        "juriste_travail", "connector_legifrance", "connector_judilibre", "connector_cdtn"
    }


def test_connector_results_are_executed_by_core_pipeline():
    result = RuntimeCoreIntegration(RuntimeIntegrationConfig(True), clock=lambda: NOW).integrate(source())
    assert result.runtime_mode is RuntimeMode.CORE_V3
    assert result.diagnostics.core_pipeline_called is True
    assert result.diagnostics.evidence_count >= result.diagnostics.connector_evidence_count


def test_connector_adapter_failure_falls_back_to_historical_sources(monkeypatch):
    class BrokenAdapter:
        def __init__(self, _source):
            pass

        def adapt(self):
            raise RuntimeError("PRIVATE-SOURCE-MUST-NOT-LEAK")

    monkeypatch.setattr(integration_module, "GenericConnectorAdapter", BrokenAdapter)
    result = RuntimeCoreIntegration(RuntimeIntegrationConfig(True), clock=lambda: NOW).integrate(source())
    assert result.runtime_mode is RuntimeMode.CORE_V3
    assert result.diagnostics.connector_fallback_triggered is True
    assert result.diagnostics.connector_fallback_code == "CONNECTOR_ADAPTER_FAILED"
    assert result.diagnostics.connector_adapter_called is True
    assert result.diagnostics.connector_count == 3
    assert result.diagnostics.connector_snapshot_count == 3
    assert result.diagnostics.connector_evidence_count == 0
    assert result.diagnostics.legal_executed is True


def test_snapshot_mapping_failure_is_non_blocking_and_deterministic():
    malformed = RuntimeConnectorPayloadMapper(RuntimeConnectorConfig(True)).map({"sources": "private"})
    result = RuntimeCoreIntegration(RuntimeIntegrationConfig(True), clock=lambda: NOW).integrate(source(malformed))
    assert result.runtime_mode is RuntimeMode.CORE_V3
    assert result.diagnostics.connector_fallback_code == "CONNECTOR_SNAPSHOT_MAPPING_FAILED"
    assert result.diagnostics.connector_adapter_called is False


def test_core_disabled_never_calls_connector_adapter(monkeypatch):
    monkeypatch.setattr(
        integration_module,
        "GenericConnectorAdapter",
        lambda _source: (_ for _ in ()).throw(AssertionError("must not be called")),
    )
    result = RuntimeCoreIntegration(RuntimeIntegrationConfig(False), clock=lambda: NOW).integrate(source())
    assert result.runtime_mode is RuntimeMode.LEGACY
    assert result.diagnostics.connector_runtime_enabled is True
    assert result.diagnostics.connector_adapter_called is False
