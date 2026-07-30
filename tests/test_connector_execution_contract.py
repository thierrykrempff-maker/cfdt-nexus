import pytest

from SYNDICAL_REASONING_ENGINE import ConnectorKind, RetrievalEvent, RetrievalStatus
from NEXUS_RUNTIME_INTEGRATION.source_execution_runtime import (
    SourceExecutionRuntime,
    SourceExecutionRuntimeConfig,
)
from tests.connector_execution_cases import plan_for


def test_live_status_requires_a_real_network_call() -> None:
    with pytest.raises(ValueError, match="live status"):
        RetrievalEvent(
            "event", "case", "plan", "issue", "target", "query", "connector",
            "Connector", ConnectorKind.LIVE_API, "LABOUR_CODE",
            RetrievalStatus.LIVE_RESULT_OBTAINED, "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00", 1, False, False, False, False,
            False, False, "query", "query", None, None, 1, 1, 0,
        )


def test_runtime_bridge_is_disabled_by_default_and_preserves_historical_path() -> None:
    result = SourceExecutionRuntime(SourceExecutionRuntimeConfig()).execute(plan_for())
    assert result.called is False
    assert result.summary is None
