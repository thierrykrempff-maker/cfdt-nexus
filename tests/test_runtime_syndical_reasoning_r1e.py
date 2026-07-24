from __future__ import annotations

from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeSyndicalReasoningConfig,
    RuntimeSyndicalReasoningIntegration,
    RuntimeSyndicalReasoningMode,
)


def runtime(**kwargs):
    return RuntimeSyndicalReasoningIntegration(RuntimeSyndicalReasoningConfig(True), timer=lambda: 1.0, **kwargs)


def test_runtime_calls_r1e_for_health_absence_case():
    result = runtime().integrate({"query": "Arrêt maladie avec IJSS, subrogation et maintien de salaire.", "route": {"domains": ["protection_sociale"]}, "sources": []})
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.domain_analysis["analysis_type"] == "health_absence_social_protection"
    assert result.domain_analysis["articulation"]["primary_domain"] == "R1E_HEALTH_ABSENCE"


def test_r1b_primary_for_absence_discipline_with_r1e_complement():
    result = runtime().integrate({"query": "Sanction pour absence dont la justification est discutée.", "route": {"domains": ["disciplinary_procedure", "absence"]}, "sources": []})
    assert result.domain_analysis["analysis_type"] == "disciplinary_procedure"
    assert result.domain_analysis["articulation"]["primary_domain"] == "R1B_DISCIPLINARY"
    assert "health_absence" in result.domain_analysis["complementary_analyses"]


def test_r1d_primary_for_harassment_with_sick_leave_and_r1e_complement():
    result = runtime().integrate({"query": "Harcèlement possible avec arrêt maladie.", "route": {"domains": ["harcelement", "protection_sociale"]}, "sources": []})
    assert result.domain_analysis["analysis_type"] == "discrimination_harassment_equal_treatment"
    assert result.domain_analysis["articulation"]["primary_domain"] == "R1D_DISCRIMINATION_HARASSMENT"
    assert "health_absence" in result.domain_analysis["complementary_analyses"]


def test_r1e_keeps_r1a_r1c_r1d_as_complementary_when_relevant():
    result = runtime().integrate({"query": "Après arrêt maladie, retrait de mission, discrimination liée à l'état de santé et baisse sur bulletin.", "route": {"domains": ["protection_sociale", "contrat_travail", "discrimination", "paie_remuneration"]}, "sources": []})
    articulation = result.domain_analysis["articulation"]
    assert articulation["primary_domain"] == "R1E_HEALTH_ABSENCE"
    assert {"R1A_CONTRACT_CHANGE", "R1C_WORKING_TIME", "R1D_DISCRIMINATION_HARASSMENT"}.issubset(set(articulation["complementary_domains"]))


def test_generic_non_employment_disease_word_does_not_activate_runtime():
    result = runtime().integrate({"query": "Cette maladie touche une plante.", "route": {"domains": ["cse"]}, "sources": []})
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.domain_analysis is None


def test_existing_feature_flag_disables_r1e():
    result = RuntimeSyndicalReasoningIntegration(RuntimeSyndicalReasoningConfig(False)).integrate({"query": "Arrêt maladie et IJSS.", "route": {"domains": ["protection_sociale"]}})
    assert result.mode is RuntimeSyndicalReasoningMode.DISABLED


def test_r1e_failure_is_fail_safe():
    class BrokenEngine:
        def analyze(self, case):
            raise RuntimeError("synthetic failure")

    result = runtime(health_absence_engine=BrokenEngine()).integrate({"query": "Arrêt maladie et IJSS.", "route": {"domains": ["protection_sociale"]}})
    assert result.mode is RuntimeSyndicalReasoningMode.FALLBACK
    assert result.diagnostics.fallback_code == "SYNDICAL_REASONING_RUNTIME_FAILED"


def test_runtime_payload_is_deterministic_confidential_and_non_calculating():
    payload = {"query": "Accident du travail déclaré et IJSS en attente.", "route": {"domains": ["at_mp", "protection_sociale"]}, "sources": []}
    integration = runtime()
    first = integration.integrate(payload)
    second = integration.integrate(payload)
    assert first.domain_analysis == second.domain_analysis
    rendered = str(first.to_dict()).lower()
    assert "calculation_performed': false" in rendered
    for forbidden in ("diagnostic détaillé", "pathologie:", "numéro de sécurité sociale", "fulltext", "chunk_id", "local_path", "c:\\"):
        assert forbidden not in rendered
