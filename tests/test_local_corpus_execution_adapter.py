from SYNDICAL_REASONING_ENGINE import (
    LocalCorpusExecutionAdapter, RetrievalStatus, SourceExecutionCoordinator, SourceFamily,
)
from tests.connector_execution_cases import plan_for


def test_local_corpus_never_claims_network_access() -> None:
    adapter = LocalCorpusExecutionAdapter(
        lambda query, context: {
            "documents": ({"id": "agreement", "title": "Accord INEOS"},)
        }
    )
    event = SourceExecutionCoordinator((adapter,)).execute(
        plan_for(SourceFamily.INEOS_AGREEMENT)
    ).events[0]
    assert event.status is RetrievalStatus.LOCAL_DOCUMENT
    assert not event.live_call_attempted
