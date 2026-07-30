from SYNDICAL_REASONING_ENGINE import (
    LegifranceExecutionAdapter, RetrievalStatus, SourceExecutionCoordinator,
)
from tests.connector_execution_cases import live_document, plan_for


def test_legifrance_wrapper_distinguishes_live_from_cache() -> None:
    adapter = LegifranceExecutionAdapter(
        transport=lambda query, context: {
            "documents": (live_document(),), "network_call_executed": True,
            "endpoint_domain": "api.piste.gouv.fr",
        },
        configured=True,
    )
    event = SourceExecutionCoordinator((adapter,)).execute(
        plan_for(), allow_network=True
    ).events[0]
    assert event.status is RetrievalStatus.LIVE_RESULT_OBTAINED
    assert event.endpoint_domain == "api.piste.gouv.fr"
