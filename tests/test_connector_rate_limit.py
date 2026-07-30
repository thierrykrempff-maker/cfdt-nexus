from SYNDICAL_REASONING_ENGINE import (
    ConnectorKind, ConnectorRateLimitError, CallableExecutionAdapter,
    SourceExecutionCoordinator, SourceFamily,
)
from tests.connector_execution_cases import plan_for


def test_rate_limit_has_a_stable_public_code() -> None:
    def limited(query, context):
        raise ConnectorRateLimitError("429")
    adapter = CallableExecutionAdapter(
        connector_id="law", connector_name="Law", connector_kind=ConnectorKind.LIVE_API,
        source_families=(SourceFamily.LABOUR_CODE,), transport=limited,
    )
    event = SourceExecutionCoordinator((adapter,)).execute(plan_for(), allow_network=True).events[0]
    assert event.error_code == "RATE_LIMITED"
    assert event.error_message_public == "La source limite temporairement les requêtes."
