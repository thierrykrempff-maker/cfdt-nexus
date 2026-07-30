from SYNDICAL_REASONING_ENGINE import (
    ConnectorKind, CallableExecutionAdapter, SourceExecutionCoordinator, SourceFamily,
)
from tests.connector_execution_cases import live_document, plan_for


def test_event_is_linked_to_plan_issue_target_and_query() -> None:
    plan = plan_for()
    adapter = CallableExecutionAdapter(
        connector_id="law", connector_name="Law", connector_kind=ConnectorKind.LIVE_API,
        source_families=(SourceFamily.LABOUR_CODE,),
        transport=lambda query, context: {
            "documents": (live_document(),), "network_call_executed": True,
        },
    )
    event = SourceExecutionCoordinator((adapter,)).execute(plan, allow_network=True).events[0]
    assert (event.plan_id, event.issue_id, event.target_id, event.query_id) == (
        "plan-1", "issue-1", "target-1", "query-1"
    )
