from SYNDICAL_REASONING_ENGINE import (
    ConnectorKind, CallableExecutionAdapter, RetrievalStatus, SourceExecutionCoordinator,
    SourceFamily,
)
from tests.connector_execution_cases import plan_for


def test_network_error_stays_local_to_the_source() -> None:
    def fail(query, context):
        raise ConnectionError("Authorization: Bearer secret-token")
    adapter = CallableExecutionAdapter(
        connector_id="law", connector_name="Law", connector_kind=ConnectorKind.LIVE_API,
        source_families=(SourceFamily.LABOUR_CODE,), transport=fail,
    )
    summary = SourceExecutionCoordinator((adapter,)).execute(plan_for(), allow_network=True)
    assert summary.events[0].status is RetrievalStatus.NETWORK_ERROR
    assert summary.documents == ()
