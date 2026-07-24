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


def test_runtime_calls_r2b_for_agenda_and_meeting_preparation():
    result = runtime().integrate(
        {
            "query": "Le secrétaire veut inscrire un point précis à l'ordre du jour du CSE.",
            "route": {"domains": ["cse"]},
            "sources": [],
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.domain_analysis["analysis_type"] == "cse_operation_meeting_preparation"
    assert result.domain_analysis["articulation"]["primary_domain"] == "R2B_CSE_OPERATION"


def test_reorganization_keeps_r2a_primary_and_r2b_complementary():
    result = runtime().integrate(
        {
            "query": "Réorganisation de plusieurs services à inscrire à l'ordre du jour CSE avec avis.",
            "route": {"domains": ["cse", "reorganisation"]},
            "sources": [],
        }
    )
    assert result.domain_analysis["analysis_type"] == "cse_information_consultation_reorganization"
    assert "cse_operation" in result.domain_analysis["complementary_analyses"]


def test_plain_non_cse_meeting_stays_unspecialized():
    result = runtime().integrate(
        {
            "query": "Comment préparer une réunion commerciale de suivi ?",
            "route": {"domains": []},
            "sources": [],
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.NOT_APPLICABLE


def test_existing_feature_flag_disables_r2b():
    result = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(False)
    ).integrate({"query": "Ordre du jour CSE.", "route": {"domains": ["cse"]}})
    assert result.mode is RuntimeSyndicalReasoningMode.DISABLED


def test_r2b_failure_is_fail_safe():
    class BrokenEngine:
        def analyze(self, case):
            raise RuntimeError("synthetic failure")

    result = runtime(cse_operation_engine=BrokenEngine()).integrate(
        {"query": "Convocation CSE et ordre du jour.", "route": {"domains": ["cse"]}}
    )
    assert result.mode is RuntimeSyndicalReasoningMode.FALLBACK
    assert result.diagnostics.fallback_code == "SYNDICAL_REASONING_RUNTIME_FAILED"


def test_runtime_output_remains_confidential_and_non_decisional():
    result = runtime().integrate(
        {
            "query": "Un document CSE est refusé pour confidentialité.",
            "route": {"domains": ["cse"]},
            "sources": [],
        }
    )
    rendered = str(result.to_dict()).lower()
    for forbidden in ("fulltext", "chunk_id", "local_path", "storage_id", "c:\\", "/home/", "délai expiré", "délit constitué"):
        assert forbidden not in rendered
