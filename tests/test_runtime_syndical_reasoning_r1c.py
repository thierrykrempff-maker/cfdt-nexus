from __future__ import annotations

from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeSyndicalReasoningConfig,
    RuntimeSyndicalReasoningIntegration,
    RuntimeSyndicalReasoningMode,
)


def runtime(**kwargs):
    return RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(True),
        timer=lambda: 1.0,
        **kwargs,
    )


def test_runtime_calls_r1c_for_standalone_working_time_case():
    result = runtime().integrate(
        {
            "query": "Écart Kelio / Nibelis sur des heures supplémentaires.",
            "route": {"domains": ["temps_travail"], "intents": []},
            "sources": [],
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.domain_analysis["analysis_type"] == "working_time"
    assert result.domain_analysis["articulation"]["primary_domain"] == "R1C_WORKING_TIME"


def test_r1a_remains_primary_for_imposed_schedule_change_with_r1c_complement():
    result = runtime().integrate(
        {
            "query": "Modification imposée des horaires et passage de jour en travail posté.",
            "route": {"domains": ["contrat_travail", "temps_travail"]},
            "sources": [],
        }
    )
    assert "detected_dimensions" in result.domain_analysis
    assert result.domain_analysis["articulation"]["primary_domain"] == "R1A_CONTRACT_CHANGE"
    assert result.domain_analysis["complementary_analyses"]["working_time"]["analysis_type"] == "working_time"


def test_r1b_remains_primary_for_sanction_after_refusal_with_r1c_complement():
    result = runtime().integrate(
        {
            "query": "Sanction après refus d'effectuer des heures supplémentaires.",
            "route": {"domains": ["disciplinary_procedure", "temps_travail"]},
            "sources": [],
        }
    )
    assert result.domain_analysis["analysis_type"] == "disciplinary_procedure"
    assert result.domain_analysis["articulation"]["primary_domain"] == "R1B_DISCIPLINARY"
    assert "working_time" in result.domain_analysis["complementary_analyses"]


def test_existing_feature_flag_disables_r1c():
    result = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(False)
    ).integrate(
        {
            "query": "Pause interrompue.",
            "route": {"domains": ["temps_travail"]},
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.DISABLED
    assert result.domain_analysis is None


def test_r1c_failure_is_fail_safe():
    class BrokenWorkingTimeEngine:
        def analyze(self, case):
            raise RuntimeError("synthetic failure")

    result = runtime(working_time_engine=BrokenWorkingTimeEngine()).integrate(
        {
            "query": "Écart Kelio / Nibelis.",
            "route": {"domains": ["temps_travail"]},
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.FALLBACK
    assert result.diagnostics.fallback_code == "SYNDICAL_REASONING_RUNTIME_FAILED"
    assert result.report is None


def test_r0_cse_question_remains_unspecialized():
    result = runtime().integrate(
        {
            "query": "Comment préparer une réunion du CSE ?",
            "route": {"domains": ["cse"], "intents": ["preparer_cse"]},
            "sources": [],
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.report is not None
    assert result.domain_analysis is None


def test_runtime_payload_is_deterministic_metadata_only_and_non_calculating():
    payload = {
        "query": "Astreinte avec intervention et repos quotidien à vérifier.",
        "route": {"domains": ["temps_travail"], "intents": []},
        "sources": [],
    }
    integration = runtime()
    first = integration.integrate(payload)
    second = integration.integrate(payload)
    assert first.domain_analysis == second.domain_analysis
    rendered = str(first.to_dict()).lower()
    assert "calculation_performed': false" in rendered
    for forbidden in ("fulltext", "local_path", "chunk_id", "storage_id", "c:\\"):
        assert forbidden not in rendered
