from __future__ import annotations

from EXPERT_PAIE_V2 import expert_paie_v2_scenarios
from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeExpertPaieV2Config,
    RuntimeExpertPaieV2Integration,
    RuntimeExpertPaieV2Mode,
)


def runtime(**kwargs):
    return RuntimeExpertPaieV2Integration(
        RuntimeExpertPaieV2Config(True), timer=lambda: 1.0, **kwargs
    )


def test_feature_flag_is_disabled_by_default_and_from_env_is_strict():
    assert not RuntimeExpertPaieV2Config().enabled
    assert RuntimeExpertPaieV2Config.from_env({"NEXUS_EXPERT_PAIE_V2_RUNTIME_ENABLED": "true"}).enabled
    assert not RuntimeExpertPaieV2Config.from_env({"NEXUS_EXPERT_PAIE_V2_RUNTIME_ENABLED": "invalid"}).enabled


def test_runtime_disabled_preserves_historical_behavior():
    result = RuntimeExpertPaieV2Integration().integrate(
        {"query": "Contrôle du bulletin", "route": {"domains": ["paie_remuneration"]}}
    )
    assert result.mode is RuntimeExpertPaieV2Mode.DISABLED


def test_runtime_ignores_non_payroll_question():
    result = runtime().integrate({"query": "Ordre du jour du CSE", "route": {"domains": ["cse"]}})
    assert result.mode is RuntimeExpertPaieV2Mode.NOT_APPLICABLE


def test_runtime_executes_supplied_synthetic_payload():
    result = runtime().integrate(
        {
            "query": "Heures supplémentaires absentes du bulletin",
            "route": {"domains": ["paie_remuneration"]},
            "expert_paie_v2_input": expert_paie_v2_scenarios()["missing_overtime"],
        }
    )
    assert result.mode is RuntimeExpertPaieV2Mode.SUCCEEDED
    assert result.analysis.to_dict()["analysis_type"] == "expert_paie_v2_control"


def test_runtime_minimal_input_refuses_calculation_safely():
    result = runtime().integrate(
        {"query": "Mes heures supplémentaires sont-elles payées ?", "route": {"domains": ["paie_remuneration"]}}
    )
    assert result.mode is RuntimeExpertPaieV2Mode.SUCCEEDED
    assert result.analysis.calculation is None
    assert result.analysis.refusals


def test_runtime_failure_falls_back_without_breaking_historical_answer():
    class BrokenEngine:
        def analyze(self, payload):
            raise RuntimeError("synthetic")

    result = runtime(engine=BrokenEngine()).integrate(
        {"query": "Bulletin de paie", "route": {"domains": ["paie_remuneration"]}}
    )
    assert result.mode is RuntimeExpertPaieV2Mode.FALLBACK
    assert result.diagnostics.fallback_code == "EXPERT_PAIE_V2_FAILED"


def test_runtime_payload_has_no_confidential_data():
    result = runtime().integrate(
        {
            "query": "Contrôle Kelio Nibelis",
            "route": {"domains": ["paie_remuneration"]},
            "expert_paie_v2_input": expert_paie_v2_scenarios()["kelio_nibelis_mismatch"],
        }
    )
    rendered = str(result.to_dict()).lower()
    for forbidden in ("nir réel", "iban", "matricule réel", "vrai salaire", "local_path", "chunk_id", "c:\\", "/home/"):
        assert forbidden not in rendered
