from __future__ import annotations

from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeSyndicalReasoningConfig,
    RuntimeSyndicalReasoningIntegration,
    RuntimeSyndicalReasoningMode,
)


def test_runtime_uses_r1a_only_for_contract_change_domain():
    result = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(True), timer=lambda: 1.0
    ).integrate(
        {
            "query": "Mon employeur modifie mes horaires et mon équipe.",
            "route": {
                "domains": ["temps_travail", "contrat_travail"],
                "intents": ["conseiller_salarie"],
            },
            "sources": [],
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.domain_analysis is not None
    assert "working_hours" in result.domain_analysis["detected_dimensions"]


def test_runtime_keeps_r0_for_other_syndical_question():
    result = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(True), timer=lambda: 1.0
    ).integrate(
        {
            "query": "Comment préparer une réunion du CSE ?",
            "route": {"domains": ["cse"], "intents": ["preparer_cse"]},
            "sources": [],
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.report is not None
    assert result.domain_analysis is None


def test_r0_feature_flag_still_disables_r1a():
    result = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(False)
    ).integrate(
        {
            "query": "Changement de poste",
            "route": {"domains": ["contrat_travail"]},
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.DISABLED
    assert result.report is None
    assert result.domain_analysis is None


def test_runtime_r1a_is_deterministic_and_metadata_only():
    payload = {
        "query": "Mutation interne avec changement de classification.",
        "route": {"domains": ["classification_carriere"], "intents": []},
        "sources": [],
    }
    integration = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(True), timer=lambda: 1.0
    )
    first = integration.integrate(payload)
    second = integration.integrate(payload)
    assert first.domain_analysis == second.domain_analysis
    assert "content" not in first.domain_analysis
