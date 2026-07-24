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


def test_runtime_calls_r1d_on_sufficient_context():
    result = runtime().integrate(
        {
            "query": "Après un mandat syndical, retrait de missions et stagnation de carrière.",
            "route": {"domains": ["discrimination", "droit_syndical"]},
            "sources": [],
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.domain_analysis["analysis_type"] == "discrimination_harassment_equal_treatment"
    assert result.domain_analysis["articulation"]["primary_domain"] == "R1D_DISCRIMINATION_HARASSMENT"


def test_simple_conflict_remains_general_and_does_not_activate_r1d():
    result = runtime().integrate(
        {
            "query": "Un désaccord isolé existe avec un responsable.",
            "route": {"domains": ["cse"]},
            "sources": [],
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.domain_analysis is None


def test_r1b_is_primary_for_sanction_after_reporting_with_r1d_complement():
    result = runtime().integrate(
        {
            "query": "Sanction peu après avoir signalé des faits : représailles possibles.",
            "route": {"domains": ["disciplinary_procedure", "discrimination"]},
            "sources": [],
        }
    )
    assert result.domain_analysis["analysis_type"] == "disciplinary_procedure"
    assert result.domain_analysis["articulation"]["primary_domain"] == "R1B_DISCIPLINARY"
    assert result.domain_analysis["complementary_analyses"]["discrimination_harassment"]["analysis_type"] == "discrimination_harassment_equal_treatment"


def test_r1a_is_primary_for_union_representative_transfer_with_r1d_complement():
    result = runtime().integrate(
        {
            "query": "Mutation imposée d'un représentant syndical après son mandat.",
            "route": {"domains": ["contrat_travail", "discrimination"]},
            "sources": [],
        }
    )
    assert "detected_dimensions" in result.domain_analysis
    assert result.domain_analysis["articulation"]["primary_domain"] == "R1A_CONTRACT_CHANGE"
    assert "discrimination_harassment" in result.domain_analysis["complementary_analyses"]


def test_r1d_can_keep_r1b_and_r1c_as_complementary_domains():
    result = runtime().integrate(
        {
            "query": "Harcèlement possible avec sanction et horaires défavorables ciblés.",
            "route": {"domains": ["discrimination", "disciplinary_procedure", "temps_travail"]},
            "sources": [],
        }
    )
    articulation = result.domain_analysis["articulation"]
    assert articulation["primary_domain"] == "R1D_DISCRIMINATION_HARASSMENT"
    assert "R1B_DISCIPLINARY" in articulation["complementary_domains"]
    assert "R1C_WORKING_TIME" in articulation["complementary_domains"]
    assert "working_time" in result.domain_analysis["complementary_analyses"]


def test_existing_feature_flag_disables_r1d():
    result = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(False)
    ).integrate(
        {
            "query": "Discrimination syndicale possible.",
            "route": {"domains": ["discrimination"]},
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.DISABLED
    assert result.domain_analysis is None


def test_r1d_failure_is_fail_safe():
    class BrokenEngine:
        def analyze(self, case):
            raise RuntimeError("synthetic failure")

    result = runtime(discrimination_engine=BrokenEngine()).integrate(
        {
            "query": "Discrimination syndicale possible.",
            "route": {"domains": ["discrimination"]},
        }
    )
    assert result.mode is RuntimeSyndicalReasoningMode.FALLBACK
    assert result.diagnostics.fallback_code == "SYNDICAL_REASONING_RUNTIME_FAILED"
    assert result.report is None


def test_runtime_payload_is_deterministic_prudent_and_confidential():
    payload = {
        "query": "Messages répétés à connotation sexuelle et signalement.",
        "route": {"domains": ["harcelement"]},
        "sources": [],
    }
    integration = runtime()
    first = integration.integrate(payload)
    second = integration.integrate(payload)
    assert first.domain_analysis == second.domain_analysis
    rendered = str(first.to_dict()).lower()
    for forbidden in (
        "harcèlement établi",
        "discrimination établie",
        "diagnostic médical",
        "fulltext",
        "local_path",
        "chunk_id",
        "storage_id",
        "c:\\",
    ):
        assert forbidden not in rendered
