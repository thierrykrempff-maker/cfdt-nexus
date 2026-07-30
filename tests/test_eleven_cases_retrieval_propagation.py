from tools.run_factual_fix_baseline import load_all_fixtures, path_for
from tools.run_real_business_cases_baseline import build_case_prompt
from NEXUS_RUNTIME_INTEGRATION import (
    RetrievalToResponseConfig,
    RetrievalToResponseIntegration,
)
from SYNDICAL_REASONING_ENGINE import build_case_factual_core
from tests.retrieval_propagation_support import RecordingRuntime


def test_eleven_cases_are_isolated_and_blocked_cases_do_not_gain_evidence(monkeypatch):
    monkeypatch.setenv("NEXUS_SOURCE_EXECUTION_COORDINATOR_ENABLED", "true")
    sessions = set()
    for fixture in load_all_fixtures():
        core = build_case_factual_core(
            build_case_prompt({"case_input": fixture["case_input"]}),
            requested_path=path_for(fixture),
        )
        sessions.add(core.origin_session_id)
        runtime = RecordingRuntime()
        result = RetrievalToResponseIntegration(
            RetrievalToResponseConfig(True), runtime=runtime
        ).integrate(core)
        if fixture["case_id"].startswith(("REAL-05", "REAL-06")):
            assert result.plan
            assert not result.plan.queries
            assert result.plan.blocked_queries
            assert not result.selection or not result.selection.selected
        else:
            assert result.called
    assert len(sessions) == 11
