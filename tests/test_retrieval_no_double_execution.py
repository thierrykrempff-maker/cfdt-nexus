from NEXUS_RUNTIME_INTEGRATION import (
    RetrievalToResponseConfig,
    RetrievalToResponseIntegration,
)
from SYNDICAL_REASONING_ENGINE import build_case_factual_core
from tests.retrieval_propagation_support import RecordingRuntime


def test_one_integration_call_executes_coordinator_exactly_once(monkeypatch):
    monkeypatch.setenv("NEXUS_SOURCE_EXECUTION_COORDINATOR_ENABLED", "true")
    runtime = RecordingRuntime()
    integration = RetrievalToResponseIntegration(
        RetrievalToResponseConfig(True), runtime=runtime
    )
    integration.integrate(
        build_case_factual_core(
            "Faits fournis:\n- Un salarié est convoqué après des courriels insultants.\n"
            "Faits reconnus:\n- Le salarié reconnaît être l'auteur des courriels."
        )
    )
    assert runtime.calls == 1
