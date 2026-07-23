from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_v1_functional_campaign.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("v1_campaign_runner_test", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def scenario():
    return {
        "id": "TEST-001", "domaine_principal": "droit_travail", "difficulte": "facile",
        "question_salarie": "Question synthétique ?", "domaines_attendus": ["contrat"],
        "experts_attendus": ["juriste_travail"], "connecteurs_attendus": ["legifrance"],
    }


class FakeServer:
    @staticmethod
    def analyze_question(_question):
        return {
            "answer": {
                "short_answer": "Réponse synthétique.",
                "route": {"main_domain": "contrat", "domains": ["contrat"]},
                "sources": [{"origin": "legifrance_code_travail", "title": "Source"}],
            },
            "expert_juriste": {"active": True}, "expert_paie": {"active": False},
            "runtime_integration": {
                "runtime_mode": "core_v3", "selected_experts": ["juriste_travail", "connector_legifrance"],
                "diagnostics": {"core_pipeline_called": True, "common_orchestrator_called": True},
            },
            "official_connectors_runtime": {"runtime_mode": "not_needed", "diagnostics": {}},
            "cse_memory_runtime": {"runtime_mode": "not_needed", "diagnostics": {}},
            "retirement_runtime": {"runtime_mode": "not_needed", "diagnostics": {}},
            "protection_sociale_runtime": {"runtime_mode": "not_needed", "diagnostics": {}},
            "analysis_report": {"sections": [{"id": "legacy", "items": ["Synthèse"]}], "markdown": "# Synthèse\n\nRésultat structuré."},
        }


def test_runner_uses_runtime_result_and_never_retains_raw_answer():
    runner = load_runner()
    record = runner.execute_one(FakeServer(), scenario())
    assert record["statut_execution"] == "success"
    assert record["experts_observes"] == ["juriste_travail"]
    assert record["connecteurs_observes"] == ["legifrance"]
    assert record["domaines_observes"] == ["contrat"]
    assert record["reponse_produite"]["raw_answer_retained"] is False
    assert "Réponse synthétique" not in str(record)
    assert record["evaluation"]["routage_principal_correct"] is True


def test_privacy_detector_reports_categories_without_values():
    runner = load_runner()
    synthetic_path = "C:" + "\\" + "Users" + "\\" + "private" + "\\" + "secret.txt"
    payload = {"diagnostic": synthetic_path, "chunk_id": "internal-42"}
    findings = runner.privacy_findings(payload)
    assert findings == (
        "absolute_windows_path",
        "internal_identifier",
        "technical_reference",
    )
    assert "private" not in str(findings)


def test_feature_profile_contains_only_existing_runtime_flags():
    runner = load_runner()
    assert set(runner.FEATURE_FLAGS) == {
        "NEXUS_CORE_RUNTIME_ENABLED", "NEXUS_CONNECTOR_RUNTIME_ENABLED",
        "NEXUS_CSE_MEMORY_RUNTIME_ENABLED", "NEXUS_RETIREMENT_RUNTIME_ENABLED",
        "NEXUS_PROTECTION_SOCIALE_RUNTIME_ENABLED", "NEXUS_OFFICIAL_CONNECTORS_RUNTIME_ENABLED",
    }
    assert set(runner.FEATURE_FLAGS.values()) == {"true"}
