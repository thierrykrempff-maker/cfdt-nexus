from __future__ import annotations

from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeSyndicalReasoningConfig,
    RuntimeSyndicalReasoningIntegration,
    RuntimeSyndicalReasoningMode,
)


def enabled_runtime():
    return RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(True), timer=lambda: 1.0
    )


def test_runtime_calls_r1b_only_for_disciplinary_domain():
    result = enabled_runtime().integrate(
        {
            "query": "Je conteste un avertissement disciplinaire.",
            "route": {"domains": ["disciplinary_procedure"], "intents": []},
            "sources": [],
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.domain_analysis["analysis_type"] == "disciplinary_procedure"
    assert result.report is not None


def test_r1b_has_priority_over_r1a_for_refusal_followed_by_sanction():
    result = enabled_runtime().integrate(
        {
            "query": "Sanction après refus d'une modification du contrat.",
            "route": {"domains": ["contrat_travail", "disciplinary_procedure"]},
            "sources": [],
        }
    )
    assert result.domain_analysis["analysis_type"] == "disciplinary_procedure"
    qualifications = {
        item["qualification"]
        for item in result.domain_analysis["qualification_candidates"]
    }
    assert "refusal_contract_change" in qualifications


def test_existing_feature_flag_disables_r1b():
    result = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(False)
    ).integrate(
        {
            "query": "Licenciement pour faute grave.",
            "route": {"domains": ["disciplinary_procedure"]},
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.DISABLED
    assert result.domain_analysis is None


def test_runtime_r1b_is_deterministic_metadata_only_and_confidential():
    payload = {
        "query": "Procédure disciplinaire visant un salarié protégé.",
        "route": {"domains": ["employee_protection"], "intents": []},
        "sources": [],
    }
    integration = enabled_runtime()
    first = integration.integrate(payload)
    second = integration.integrate(payload)
    assert first.domain_analysis == second.domain_analysis
    rendered = str(first.to_dict()).lower()
    for forbidden in ("fulltext", "local_path", "chunk_id", "storage_id", "c:\\"):
        assert forbidden not in rendered


def test_non_disciplinary_contract_case_still_uses_r1a():
    result = enabled_runtime().integrate(
        {
            "query": "Mon employeur modifie durablement mes horaires.",
            "route": {"domains": ["temps_travail", "contrat_travail"]},
            "sources": [],
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert "detected_dimensions" in result.domain_analysis
    assert "analysis_type" not in result.domain_analysis
