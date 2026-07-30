from SYNDICAL_REASONING_ENGINE import (
    CSECSSCTExecutionAdapter,
    RetrievalStatus,
    SourceExecutionCoordinator,
)
from tests.cse_cssct_test_support import corpus, plan


def test_blocked_query_is_never_executed(tmp_path):
    adapter = CSECSSCTExecutionAdapter(corpus(tmp_path))
    summary = SourceExecutionCoordinator((adapter,)).execute(plan(blocked=True))
    assert summary.executed_queries == 0
    assert summary.events[0].status is RetrievalStatus.BLOCKED_BY_MISSING_FACTS
