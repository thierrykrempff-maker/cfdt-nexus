from SYNDICAL_REASONING_ENGINE import (
    ConnectorKind, CallableExecutionAdapter, RetrievalStatus, SourceExecutionCoordinator,
    SourceFamily,
)
from tests.connector_execution_cases import plan_for


def test_blocked_query_is_never_executed() -> None:
    calls = []
    adapter = CallableExecutionAdapter(
        connector_id="law", connector_name="Law", connector_kind=ConnectorKind.LIVE_API,
        source_families=(SourceFamily.LABOUR_CODE,),
        transport=lambda query, context: calls.append(True) or {},
    )
    event = SourceExecutionCoordinator((adapter,)).execute(
        plan_for(blocked=True), allow_network=True
    ).events[0]
    assert event.status is RetrievalStatus.BLOCKED_BY_MISSING_FACTS
    assert not calls
