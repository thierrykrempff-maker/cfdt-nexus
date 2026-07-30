from SYNDICAL_REASONING_ENGINE import (
    ConnectorKind, CallableExecutionAdapter, RetrievalStatus, SourceExecutionCoordinator,
    SourceFamily,
)
from tests.connector_execution_cases import plan_for


def test_unconfigured_connector_is_not_called() -> None:
    called = []
    adapter = CallableExecutionAdapter(
        connector_id="law", connector_name="Law", connector_kind=ConnectorKind.LIVE_API,
        source_families=(SourceFamily.LABOUR_CODE,),
        transport=lambda query, context: called.append(True), configured=False,
    )
    event = SourceExecutionCoordinator((adapter,)).execute(plan_for(), allow_network=True).events[0]
    assert event.status is RetrievalStatus.CONNECTOR_NOT_CONFIGURED
    assert called == []
