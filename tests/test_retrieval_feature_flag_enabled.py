from NEXUS_RUNTIME_INTEGRATION import (
    RetrievalToResponseConfig,
    RetrievalToResponseIntegration,
)
from SYNDICAL_REASONING_ENGINE import build_case_factual_core
from tests.retrieval_propagation_support import RecordingRuntime


def test_enabled_flag_executes_and_selects_safe_evidence(monkeypatch):
    monkeypatch.setenv("NEXUS_SOURCE_EXECUTION_COORDINATOR_ENABLED", "true")
    runtime = RecordingRuntime()
    result = RetrievalToResponseIntegration(
        RetrievalToResponseConfig(True), runtime=runtime
    ).integrate(
        build_case_factual_core(
            "Faits fournis:\n- Un salarié est convoqué après des courriels insultants.\n"
            "Faits reconnus:\n- Le salarié reconnaît être l'auteur des courriels.\n"
            "Informations manquantes:\n- Le contenu exact des courriels"
        )
    )
    assert result.called
    assert result.selection
    assert len(result.selection.selected) == 1
    assert runtime.calls == 1
