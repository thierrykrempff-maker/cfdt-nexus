from __future__ import annotations

from copy import deepcopy

from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeFinalAssistantConfig,
    RuntimeFinalAssistantIntegration,
    RuntimeFinalAssistantMode,
)


def answer(query="Sanction après refus d'horaire"):
    return {
        "query": query,
        "route": {"domains": ["disciplinaire", "temps_travail"]},
        "sources": [{"type": "official", "title": "Code du travail"}],
    }


def report():
    return {"title": "Rapport historique", "sections": [{"id": "legacy", "items": ["inchangé"]}]}


def test_feature_flag_is_disabled_by_default_and_strict():
    assert not RuntimeFinalAssistantConfig().enabled
    assert RuntimeFinalAssistantConfig.from_env({"NEXUS_FINAL_ASSISTANT_RUNTIME_ENABLED": "true"}).enabled
    assert not RuntimeFinalAssistantConfig.from_env({"NEXUS_FINAL_ASSISTANT_RUNTIME_ENABLED": "invalid"}).enabled


def test_disabled_runtime_preserves_exact_historical_report():
    original = report()
    result = RuntimeFinalAssistantIntegration().integrate(answer(), original)
    assert result.mode is RuntimeFinalAssistantMode.DISABLED
    assert result.report is original


def test_enabled_runtime_adds_final_assistant_section():
    result = RuntimeFinalAssistantIntegration(
        RuntimeFinalAssistantConfig(True), timer=lambda: 1.0
    ).integrate(
        answer(),
        report(),
        existing_results={
            "syndical_reasoning": {"mode": "SUCCEEDED"},
            "cse_memory": {"mode": "DISABLED"},
        },
    )
    assert result.mode is RuntimeFinalAssistantMode.SUCCEEDED
    assert result.assistant["primary_domain"] == "discipline"
    assert any(section["id"] == "nexus_final_assistant" for section in result.report["sections"])


def test_specialized_flags_are_respected_and_payroll_is_not_implicitly_enabled():
    payroll_answer = answer("Bulletin de paie incompris")
    payroll_answer["route"] = {"domains": ["paie_remuneration"]}
    result = RuntimeFinalAssistantIntegration(RuntimeFinalAssistantConfig(True)).integrate(
        payroll_answer, report()
    )
    assert result.mode is RuntimeFinalAssistantMode.SUCCEEDED
    assert result.assistant["trace"]["engines_called"] == ["expert_paie_v2"]
    assert result.assistant["confidence"] == "LOW"


def test_runtime_failure_returns_exact_historical_report(monkeypatch):
    original = report()
    integration = RuntimeFinalAssistantIntegration(RuntimeFinalAssistantConfig(True))
    monkeypatch.setattr(
        "NEXUS_RUNTIME_INTEGRATION.final_assistant_runtime._request_from_answer",
        lambda _: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    result = integration.integrate(answer(), original)
    assert result.mode is RuntimeFinalAssistantMode.FALLBACK
    assert result.report is original
    assert result.diagnostics.fallback_code == "FINAL_ASSISTANT_RUNTIME_FAILED"


def test_runtime_does_not_mutate_historical_report_or_existing_results():
    original = report()
    baseline = deepcopy(original)
    existing = {"syndical_reasoning": {"mode": "SUCCEEDED"}}
    RuntimeFinalAssistantIntegration(RuntimeFinalAssistantConfig(True)).integrate(
        answer(), original, existing_results=existing
    )
    assert original == baseline
    assert existing == {"syndical_reasoning": {"mode": "SUCCEEDED"}}


def test_runtime_public_payload_contains_no_paths_or_internal_ids():
    result = RuntimeFinalAssistantIntegration(RuntimeFinalAssistantConfig(True)).integrate(
        answer(), report()
    )
    rendered = str(result.to_dict()).lower()
    for forbidden in ("chunk_id", "storage_id", "local_path", "c:\\", "/home/", "/tmp/"):
        assert forbidden not in rendered
