from SYNDICAL_REASONING_ENGINE import (
    ConnectorKind, CallableExecutionAdapter, RetrievalStatus, SourceExecutionCoordinator,
    SourceFamily,
)
from tests.connector_execution_cases import live_document, plan_for


def test_metadata_is_never_reported_as_live() -> None:
    adapter = CallableExecutionAdapter(
        connector_id="catalog", connector_name="Catalog",
        connector_kind=ConnectorKind.STATIC_CATALOG,
        source_families=(SourceFamily.LABOUR_CODE,),
        transport=lambda query, context: {"documents": (live_document(),), "metadata_only": True},
    )
    event = SourceExecutionCoordinator((adapter,)).execute(plan_for()).events[0]
    assert event.status is RetrievalStatus.METADATA_ONLY
    assert not event.network_call_executed
