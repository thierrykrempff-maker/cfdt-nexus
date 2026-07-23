from __future__ import annotations

import json

from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeCoreIntegration,
    RuntimeCoreIntegrationInput,
    RuntimeCoreIntegrationResult,
    RuntimeCoreReportMapper,
    RuntimeIntegrationConfig,
    RuntimeMode,
)
from NEXUS_RUNTIME_INTEGRATION.models import RuntimeCoreIntegrationDiagnostics


def test_report_is_unchanged_in_legacy_and_fallback_modes():
    report = {"sections": [{"id": "legacy", "title": "Historique", "items": ["Conservé"]}], "markdown": "legacy"}
    mapper = RuntimeCoreReportMapper()
    legacy = RuntimeCoreIntegrationResult(RuntimeMode.LEGACY, RuntimeCoreIntegrationDiagnostics(False))
    fallback = RuntimeCoreIntegrationResult(
        RuntimeMode.CORE_V3_FALLBACK,
        RuntimeCoreIntegrationDiagnostics(True, fallback_triggered=True, fallback_code="TEST_FALLBACK"),
    )
    assert mapper.map(report, legacy) is report
    assert mapper.map(report, fallback) is report


def test_core_report_adds_only_a_delimited_section():
    report = {
        "sections": [{"id": "legacy", "title": "Historique", "items": ["Conservé"]}],
        "generated_from": ["legacy"],
        "markdown": "legacy",
    }
    integration = RuntimeCoreIntegrationResult(
        RuntimeMode.CORE_V3,
        RuntimeCoreIntegrationDiagnostics(True, core_pipeline_called=True, common_orchestrator_called=True),
        report_items=("Preuves transmises : 2.",),
    )
    mapped = RuntimeCoreReportMapper().map(report, integration)
    assert report["sections"] == [{"id": "legacy", "title": "Historique", "items": ["Conservé"]}]
    assert mapped["sections"][0] == report["sections"][0]
    assert mapped["sections"][-1]["id"] == "core_v3_runtime"
    assert "Preuves transmises : 2." in mapped["markdown"]


def test_diagnostics_never_expose_sensitive_fixture_values():
    sensitive_values = (
        "Personne Exemple",
        "synthetic.person@example.invalid",
        "+33 6 00 00 00 00",
        "FR7630006000011234567890189",
        "299019999999999",
        "MATRICULE-SYNTHETIQUE-42",
        "ADRESSE-SYNTHETIQUE",
        "SALAIRE-SYNTHETIQUE",
    )
    question = " ".join(sensitive_values)
    result = RuntimeCoreIntegration(RuntimeIntegrationConfig(True)).integrate(
        RuntimeCoreIntegrationInput(
            {"query": question, "route": {"main_domain": "paie", "domains": ["paie_remuneration"]}},
            {"active": False},
            {
                "active": True,
                "name": "Expert Paie V0",
                "objet_du_controle": "Contrôle sans valeur réelle.",
                "elements_du_bulletin_concernes": [],
                "donnees_necessaires_au_calcul": [],
                "limites": [],
            },
            {},
        )
    )
    serialized = json.dumps(result.to_dict(), ensure_ascii=False)
    assert result.runtime_mode is RuntimeMode.CORE_V3
    for value in sensitive_values:
        assert value not in serialized


def test_malformed_sensitive_payload_does_not_escape_in_fallback():
    result = RuntimeCoreIntegration(RuntimeIntegrationConfig(True)).integrate(
        RuntimeCoreIntegrationInput(
            {"query": "Question synthétique", "route": {"main_domain": "paie", "domains": ["paie_remuneration"]}},
            {"active": False},
            "SECRET-SYNTHETIQUE-NE-PAS-EXPOSER",
            {},
        )
    )
    serialized = json.dumps(result.to_dict(), ensure_ascii=False)
    assert result.runtime_mode is RuntimeMode.CORE_V3_FALLBACK
    assert "SECRET-SYNTHETIQUE-NE-PAS-EXPOSER" not in serialized
    assert "Traceback" not in serialized
