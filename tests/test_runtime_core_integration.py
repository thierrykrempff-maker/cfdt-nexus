from __future__ import annotations

from datetime import datetime, timezone

import pytest

import NEXUS_RUNTIME_INTEGRATION.integration as integration_module
from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeCoreIntegration,
    RuntimeCoreIntegrationInput,
    RuntimeIntegrationConfig,
    RuntimeMode,
)


NOW = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)


def answer(question="Question synthétique", domains=("paie_remuneration",)):
    return {
        "query": question,
        "confidence": "moyen",
        "route": {"main_domain": domains[0], "domains": list(domains)},
        "sources": [{"origin": "synthetic", "document": "Source synthétique", "source_layer": "autre"}],
    }


def legal(active=True):
    return {
        "active": active,
        "ce_qui_est_certain": ["Un contrôle humain reste nécessaire."],
        "conclusion_provisoire_juridique": {"position": "Vérification requise."},
        "strategie_action_ordonnee": ["Relire les sources applicables."],
        "questions_a_poser_direction": ["Quelle règle est appliquée ?"],
        "niveau_de_confiance": "moyen",
        "limites": [],
    }


def payroll(active=True):
    return {
        "active": active,
        "name": "Expert Paie V0",
        "objet_du_controle": "Contrôle synthétique de rubrique.",
        "elements_du_bulletin_concernes": ["rubrique_synthetique"],
        "methode_de_controle": ["Comparer les données disponibles."],
        "donnees_necessaires_au_calcul": [],
        "niveau_de_confiance": "moyen",
        "limites": [],
        "sources_utilisees": [],
    }


def source(legal_payload=None, payroll_payload=None, question="Question synthétique"):
    return RuntimeCoreIntegrationInput(
        answer(question),
        legal() if legal_payload is None else legal_payload,
        payroll() if payroll_payload is None else payroll_payload,
        {"reponse_synthetique_nexus": "Réponse historique conservée."},
    )


def runtime(enabled=True):
    return RuntimeCoreIntegration(RuntimeIntegrationConfig(enabled), clock=lambda: NOW)


def test_disabled_configuration_is_strict_legacy_mode():
    result = runtime(False).integrate(source())
    assert result.runtime_mode is RuntimeMode.LEGACY
    assert result.diagnostics.core_enabled is False
    assert result.diagnostics.payroll_adapter_called is False


def test_legal_only_uses_core_and_common_orchestrator_without_payroll_adapter():
    result = runtime().integrate(source(payroll_payload={"active": False}))
    assert result.runtime_mode is RuntimeMode.CORE_V3
    assert result.diagnostics.legal_executed is True
    assert result.diagnostics.payroll_executed is False
    assert result.diagnostics.core_pipeline_called is True
    assert result.diagnostics.common_orchestrator_called is True
    assert result.selected_experts == ("juriste_travail",)


def test_payroll_only_calls_real_payroll_adapter_and_common_orchestrator(monkeypatch):
    calls = {"payroll": 0, "common": 0}
    real_payroll = integration_module.PayrollAdapter
    real_common = integration_module.CommonExpertOrchestrator

    class TrackedPayroll(real_payroll):
        def adapt(self):
            calls["payroll"] += 1
            return super().adapt()

    class TrackedCommon(real_common):
        def execute(self, request):
            calls["common"] += 1
            return super().execute(request)

    monkeypatch.setattr(integration_module, "PayrollAdapter", TrackedPayroll)
    monkeypatch.setattr(integration_module, "CommonExpertOrchestrator", TrackedCommon)
    result = runtime().integrate(source(legal_payload={"active": False}))
    assert result.runtime_mode is RuntimeMode.CORE_V3
    assert result.diagnostics.payroll_adapter_called is True
    assert result.diagnostics.common_orchestrator_called is True
    assert calls["payroll"] >= 1
    assert calls["common"] == 1
    assert result.selected_experts == ("paie",)


def test_mixed_question_aggregates_legal_and_payroll():
    result = runtime().integrate(source())
    assert result.runtime_mode is RuntimeMode.CORE_V3
    assert result.selected_experts == ("juriste_travail", "paie")
    assert result.diagnostics.evidence_count >= 2
    assert result.diagnostics.finding_count >= 2


@pytest.mark.parametrize(
    "question",
    (
        "Ma classification a-t-elle une incidence salariale ?",
        "Mes heures supplémentaires ne sont pas payées.",
        "Ma prime semble mal calculée.",
    ),
)
def test_required_payroll_scenarios_traverse_core(question):
    result = runtime().integrate(source(question=question))
    assert result.runtime_mode is RuntimeMode.CORE_V3
    assert result.diagnostics.payroll_adapter_called is True
    assert result.diagnostics.core_pipeline_called is True


def test_malformed_payroll_payload_triggers_clean_fallback():
    result = runtime().integrate(source(payroll_payload="malformed"))
    assert result.runtime_mode is RuntimeMode.CORE_V3_FALLBACK
    assert result.diagnostics.fallback_triggered is True
    assert result.diagnostics.fallback_code == "RUNTIME_PAYROLL_PAYLOAD_MALFORMED"


def test_absent_experts_trigger_clean_fallback():
    result = runtime().integrate(source({"active": False}, {"active": False}))
    assert result.runtime_mode is RuntimeMode.CORE_V3_FALLBACK
    assert result.diagnostics.fallback_code == "NO_RUNTIME_EXPERT_PAYLOAD"


def test_failed_payroll_expert_triggers_fallback_without_raising():
    failed = payroll()
    failed["errors"] = ["Erreur synthétique contrôlée."]
    result = runtime().integrate(source(legal_payload={"active": False}, payroll_payload=failed))
    assert result.runtime_mode is RuntimeMode.CORE_V3_FALLBACK
    assert result.diagnostics.fallback_code == "PAYROLL_EXPERT_UNAVAILABLE"


def test_core_error_does_not_escape_and_returns_fallback(monkeypatch):
    monkeypatch.setattr(RuntimeCoreIntegration, "_run_core", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("synthetic")))
    result = runtime().integrate(source())
    assert result.runtime_mode is RuntimeMode.CORE_V3_FALLBACK
    assert result.diagnostics.fallback_code == "CORE_RUNTIME_INTEGRATION_FAILED"
