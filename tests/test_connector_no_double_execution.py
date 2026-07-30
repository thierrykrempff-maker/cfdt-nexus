from SYNDICAL_REASONING_ENGINE import (
    ConnectorKind, CallableExecutionAdapter, SourceExecutionCoordinator, SourceFamily,
)
from tests.connector_execution_cases import live_document, plan_for


def test_distinct_sessions_do_not_share_execution_state() -> None:
    calls = []
    adapter = CallableExecutionAdapter(
        connector_id="law", connector_name="Law", connector_kind=ConnectorKind.LIVE_API,
        source_families=(SourceFamily.LABOUR_CODE,),
        transport=lambda query, context: calls.append(context.case_session_id) or {
            "documents": (live_document(),), "network_call_executed": True,
        },
    )
    coordinator = SourceExecutionCoordinator((adapter,))
    coordinator.execute(plan_for(case_session_id="one"), allow_network=True)
    coordinator.execute(plan_for(case_session_id="two"), allow_network=True)
    assert calls == ["one", "two"]
