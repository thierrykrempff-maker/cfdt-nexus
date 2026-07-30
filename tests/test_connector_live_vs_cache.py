from SYNDICAL_REASONING_ENGINE import (
    ConnectorCacheCorruptedError, ConnectorKind, CallableExecutionAdapter,
    RetrievalStatus, SourceExecutionCoordinator, SourceFamily,
)
from tests.connector_execution_cases import live_document, plan_for


def test_cache_and_stale_cache_are_explicit() -> None:
    for stale, expected in (
        (False, RetrievalStatus.CACHE_RESULT),
        (True, RetrievalStatus.STALE_CACHE_RESULT),
    ):
        adapter = CallableExecutionAdapter(
            connector_id=f"cache-{stale}", connector_name="Cache",
            connector_kind=ConnectorKind.CACHE_BACKED_API,
            source_families=(SourceFamily.LABOUR_CODE,),
            transport=lambda query, context, stale=stale: {
                "documents": (live_document(),), "cache_hit": True, "stale": stale,
                "network_call_executed": False,
            },
        )
        event = SourceExecutionCoordinator((adapter,)).execute(
            plan_for(case_session_id=f"cache-{stale}"), allow_network=True
        ).events[0]
        assert event.status is expected
        assert not event.network_call_executed


def test_corrupted_cache_is_an_explicit_error_not_a_live_result() -> None:
    def corrupted(query, context):
        raise ConnectorCacheCorruptedError("private cache path")
    adapter = CallableExecutionAdapter(
        connector_id="cache", connector_name="Cache",
        connector_kind=ConnectorKind.CACHE_BACKED_API,
        source_families=(SourceFamily.LABOUR_CODE,),
        transport=corrupted,
    )
    event = SourceExecutionCoordinator((adapter,)).execute(
        plan_for(), allow_network=True
    ).events[0]
    assert event.status is RetrievalStatus.CONNECTOR_ERROR
    assert event.error_code == "CACHE_CORRUPTED"
    assert not event.network_call_executed
