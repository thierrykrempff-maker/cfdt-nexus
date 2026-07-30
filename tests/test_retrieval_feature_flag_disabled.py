from NEXUS_RUNTIME_INTEGRATION import (
    RetrievalToResponseConfig,
    RetrievalToResponseIntegration,
    build_final_response,
)
from SYNDICAL_REASONING_ENGINE import build_case_factual_core
from tests.retrieval_propagation_support import RecordingRuntime


def test_disabled_flag_preserves_old_pipeline_without_execution():
    runtime = RecordingRuntime()
    result = RetrievalToResponseIntegration(
        RetrievalToResponseConfig(False), runtime=runtime
    ).integrate(build_case_factual_core("Une sanction est envisagée."))
    assert not result.called
    assert result.plan is None
    assert runtime.calls == 0


def test_disabled_pipeline_adds_no_retrieval_projection():
    response = build_final_response({"short_answer": "Réponse historique."})
    assert "retrieval_summary" not in response["detailed_analysis"]
    assert "retrieved_sources" not in response["public_summary"]
    assert "cse_context" not in response["public_summary"]
