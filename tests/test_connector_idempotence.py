from SYNDICAL_REASONING_ENGINE import (
    ConnectorKind, CallableExecutionAdapter, SourceExecutionCoordinator, SourceFamily,
)
from tests.connector_execution_cases import live_document, plan_for


def test_same_session_query_connector_and_version_is_idempotent() -> None:
    calls = []
    adapter = CallableExecutionAdapter(
        connector_id="law", connector_name="Law", connector_kind=ConnectorKind.LIVE_API,
        source_families=(SourceFamily.LABOUR_CODE,),
        transport=lambda query, context: calls.append(query.query_id) or {
            "documents": (live_document(),), "network_call_executed": True,
        },
    )
    coordinator = SourceExecutionCoordinator((adapter,))
    coordinator.execute(plan_for(), allow_network=True)
    second = coordinator.execute(plan_for(), allow_network=True)
    assert calls == ["query-1"]
    assert second.duplicate_calls_avoided == 1
