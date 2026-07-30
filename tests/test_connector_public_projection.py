from SYNDICAL_REASONING_ENGINE import (
    ConnectorKind, CallableExecutionAdapter, SourceExecutionCoordinator, SourceFamily,
)
from tests.connector_execution_cases import live_document, plan_for


def test_public_projection_is_readable_and_technical_ids_are_hidden() -> None:
    adapter = CallableExecutionAdapter(
        connector_id="law", connector_name="Légifrance", connector_kind=ConnectorKind.LIVE_API,
        source_families=(SourceFamily.LABOUR_CODE,),
        transport=lambda query, context: {
            "documents": (live_document(),), "network_call_executed": True,
        },
    )
    public = SourceExecutionCoordinator((adapter,)).execute(
        plan_for(), allow_network=True
    ).to_dict(public=True)
    assert public["title"] == "Recherches effectuées"
    assert public["sources"][0]["search_live"] is True
    assert "event_id" not in public["sources"][0]
