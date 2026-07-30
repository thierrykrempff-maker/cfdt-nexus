from SYNDICAL_REASONING_ENGINE import (
    CSECSSCTExecutionAdapter,
    ConnectorKind,
    RetrievalStatus,
    SourceExecutionCoordinator,
)
from tests.cse_cssct_test_support import corpus, plan


def test_lot3_coordinator_routes_cse_queries_to_local_index(tmp_path):
    summary = SourceExecutionCoordinator((CSECSSCTExecutionAdapter(corpus(tmp_path)),)).execute(
        plan()
    )
    assert summary.events[0].connector_kind is ConnectorKind.LOCAL_INDEX
    assert summary.events[0].status is RetrievalStatus.LOCAL_DOCUMENT
    assert summary.events[0].network_call_executed is False
    assert summary.local_results == 1


def test_internal_practice_is_routed_to_the_same_traceable_local_adapter(tmp_path):
    from SYNDICAL_REASONING_ENGINE import SourceFamily
    from tests.cse_cssct_test_support import research_query

    query, target = research_query(family=SourceFamily.INTERNAL_PRACTICE)
    adapter = CSECSSCTExecutionAdapter(corpus(tmp_path))
    assert adapter.can_handle(query, target) is True


def test_runtime_coordinator_and_corpus_are_disabled_without_configuration(monkeypatch):
    from NEXUS_RUNTIME_INTEGRATION.source_execution_runtime import (
        ENV_CSE_PROCESSED_ROOT,
        ENV_ENABLED,
        SourceExecutionRuntimeConfig,
    )

    monkeypatch.delenv(ENV_ENABLED, raising=False)
    monkeypatch.delenv(ENV_CSE_PROCESSED_ROOT, raising=False)
    config = SourceExecutionRuntimeConfig.from_env()
    assert config.enabled is False
    assert config.cse_processed_root is None
