from __future__ import annotations

from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeSyndicalReasoningConfig,
    RuntimeSyndicalReasoningIntegration,
    RuntimeSyndicalReasoningMode,
)


def runtime(**kwargs):
    return RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(True), timer=lambda: 1.0, **kwargs
    )


def test_runtime_calls_r2c_for_collective_claim_and_investigation():
    result = runtime().integrate(
        {
            "query": "Plusieurs salariés signalent au CSE des faits répétés et demandent une enquête CSE.",
            "route": {"domains": ["cse"]},
            "sources": [],
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.domain_analysis["analysis_type"] == "cse_claims_alerts_expertise"
    assert result.domain_analysis["articulation"]["primary_domain"] == "R2C_CSE_ALERTS_EXPERTISE"


def test_r2a_remains_primary_and_r2c_is_complementary_for_important_project():
    result = runtime().integrate(
        {
            "query": "Réorganisation et projet important présentés au CSE avec expertise potentielle.",
            "route": {"domains": ["cse", "reorganisation"]},
            "sources": [],
        }
    )
    assert result.domain_analysis["analysis_type"] == "cse_information_consultation_reorganization"
    assert "cse_alerts_expertise" in result.domain_analysis["complementary_analyses"]


def test_r2b_remains_available_for_plain_agenda_operation():
    result = runtime().integrate(
        {"query": "Inscrire un point à l'ordre du jour du CSE.", "route": {"domains": ["cse"]}}
    )
    assert result.domain_analysis["analysis_type"] == "cse_operation_meeting_preparation"


def test_plain_alert_word_does_not_activate_r2c():
    result = runtime().integrate(
        {"query": "Une alerte de stock est évoquée en réunion commerciale.", "route": {"domains": []}}
    )
    assert result.mode is RuntimeSyndicalReasoningMode.NOT_APPLICABLE


def test_isolated_individual_claim_does_not_activate_r2c():
    result = runtime().integrate(
        {"query": "Un salarié présente un cas individuel isolé au CSE.", "route": {"domains": ["cse"]}}
    )
    assert not result.domain_analysis or result.domain_analysis.get("analysis_type") != "cse_claims_alerts_expertise"


def test_existing_feature_flag_disables_r2c():
    result = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(False)
    ).integrate({"query": "Alerte économique potentielle au CSE.", "route": {"domains": ["cse"]}})
    assert result.mode is RuntimeSyndicalReasoningMode.DISABLED


def test_r2c_failure_is_fail_safe():
    class BrokenEngine:
        def analyze(self, case):
            raise RuntimeError("synthetic failure")

    result = runtime(cse_alerts_engine=BrokenEngine()).integrate(
        {"query": "Plusieurs salariés demandent au CSE une enquête sur des faits répétés.", "route": {"domains": ["cse"]}}
    )
    assert result.mode is RuntimeSyndicalReasoningMode.FALLBACK
    assert result.diagnostics.fallback_code == "SYNDICAL_REASONING_RUNTIME_FAILED"


def test_runtime_output_is_confidential_and_non_decisional():
    result = runtime().integrate(
        {"query": "Le CSE envisage un droit d'alerte économique et une expertise.", "route": {"domains": ["cse"]}}
    )
    rendered = str(result.to_dict()).lower()
    for forbidden in (
        "fulltext",
        "chunk_id",
        "local_path",
        "storage_id",
        "c:\\",
        "/home/",
        "expertise acquise",
        "financement certain",
        "alerte constituée",
    ):
        assert forbidden not in rendered
