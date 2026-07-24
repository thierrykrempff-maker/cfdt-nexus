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


def test_runtime_calls_r2a_for_collective_reorganization():
    result = runtime().integrate(
        {
            "query": "Réorganisation de plusieurs services avec suppression de postes et consultation à vérifier.",
            "route": {"domains": ["cse", "reorganisation"]},
            "sources": [],
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.domain_analysis["analysis_type"] == "cse_information_consultation_reorganization"
    assert result.domain_analysis["articulation"]["primary_domain"] == "R2A_CSE_CONSULTATION"


def test_runtime_keeps_r1a_primary_for_purely_individual_case():
    result = runtime().integrate(
        {
            "query": "Un seul salarié change de poste, sans autre indice collectif.",
            "route": {"domains": ["cse", "contrat_travail"]},
            "sources": [],
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.domain_analysis is not None
    assert result.domain_analysis.get("analysis_type") != "cse_information_consultation_reorganization"
    assert "cse_consultation" not in result.domain_analysis.get("complementary_analyses", {})


def test_runtime_articulates_collective_hours_with_r1c():
    result = runtime().integrate(
        {
            "query": "Plusieurs équipes changent de cycle et d'horaires dans un projet collectif.",
            "route": {"domains": ["cse", "temps_travail"]},
            "sources": [],
        }
    )
    assert result.domain_analysis["articulation"]["primary_domain"] == "R2A_CSE_CONSULTATION"
    assert "R1C_WORKING_TIME" in result.domain_analysis["articulation"]["complementary_domains"]


def test_existing_feature_flag_disables_r2a():
    result = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(False)
    ).integrate({"query": "Réorganisation du service.", "route": {"domains": ["cse"]}})
    assert result.mode is RuntimeSyndicalReasoningMode.DISABLED


def test_r2a_failure_is_fail_safe():
    class BrokenEngine:
        def analyze(self, case):
            raise RuntimeError("synthetic failure")

    result = runtime(cse_consultation_engine=BrokenEngine()).integrate(
        {"query": "Réorganisation de plusieurs services.", "route": {"domains": ["cse"]}}
    )
    assert result.mode is RuntimeSyndicalReasoningMode.FALLBACK
    assert result.diagnostics.fallback_code == "SYNDICAL_REASONING_RUNTIME_FAILED"


def test_runtime_payload_is_confidential_and_non_decisional():
    result = runtime().integrate(
        {
            "query": "Le CSE n'a pas été consulté et la mise en œuvre a commencé.",
            "route": {"domains": ["cse", "reorganisation"]},
            "sources": [],
        }
    )
    rendered = str(result.to_dict()).lower()
    for forbidden in ("fulltext", "chunk_id", "local_path", "c:\\", "/home/", "délit constitué"):
        assert forbidden not in rendered
