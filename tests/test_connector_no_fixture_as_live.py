from SYNDICAL_REASONING_ENGINE import (
    ConnectorKind, CallableExecutionAdapter, RetrievalStatus, SourceExecutionCoordinator,
    SourceFamily,
)
from tests.connector_execution_cases import live_document, plan_for


def test_fixture_is_never_live() -> None:
    adapter = CallableExecutionAdapter(
        connector_id="fixture", connector_name="Fixture",
        connector_kind=ConnectorKind.FIXTURE_PROVIDER,
        source_families=(SourceFamily.LABOUR_CODE,),
        transport=lambda query, context: {"documents": (live_document(),), "fixture": True},
    )
    event = SourceExecutionCoordinator((adapter,)).execute(plan_for()).events[0]
    assert event.status is RetrievalStatus.FIXTURE_RESULT
    assert event.fixture_used and not event.live_call_attempted
