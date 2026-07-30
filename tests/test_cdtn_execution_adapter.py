from SYNDICAL_REASONING_ENGINE import (
    CdtnExecutionAdapter, RetrievalStatus, SourceExecutionCoordinator, SourceFamily,
)
from tests.connector_execution_cases import plan_for


def test_cdtn_wrapper_reports_live_no_relevant_result() -> None:
    adapter = CdtnExecutionAdapter(
        transport=lambda query, context: {"documents": (), "network_call_executed": True}
    )
    result = SourceExecutionCoordinator((adapter,)).execute(
        plan_for(SourceFamily.OFFICIAL_GUIDANCE, query_text="procédure officielle"),
        allow_network=True,
    )
    assert result.events[0].status is RetrievalStatus.LIVE_NO_RELEVANT_RESULT
