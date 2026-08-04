from NEXUS_RUNTIME_INTEGRATION.retrieval_to_response import (
    RetrievalToResponseConfig,
    RetrievalToResponseIntegration,
)
from NEXUS_RUNTIME_INTEGRATION.source_execution_runtime import (
    SourceExecutionRuntime,
    SourceExecutionRuntimeConfig,
)
from SYNDICAL_REASONING_ENGINE import (
    PlanningStatus,
    RetrievalStatus,
    SourceFamily,
    build_case_factual_core,
    build_research_plan,
)
from tests.cse_cssct_test_support import corpus


CSE_HISTORY_QUESTION = (
    "Que disent les anciens PV CSE sur la modification des horaires "
    "et le passage au travail en équipes ?"
)


def _plan(question: str):
    core = build_case_factual_core(question, origin_session_id="documentary-cse")
    return core, build_research_plan(core)


def test_explicit_cse_history_question_creates_a_local_minutes_query() -> None:
    _core, plan = _plan(CSE_HISTORY_QUESTION)

    assert len(plan.issues) == 1
    assert plan.issues[0].created_from_rules == ("cse-documentary-history",)
    assert plan.issues[0].requires_cse_search is True
    assert {target.source_family for target in plan.targets} == {
        SourceFamily.CSE_MINUTES
    }
    assert len(plan.queries) == 1
    assert plan.queries[0].status is PlanningStatus.READY
    assert {"modification", "horaires", "passage", "equipes"}.issubset(
        set(plan.queries[0].concepts)
    )


def test_cse_word_alone_does_not_create_a_documentary_history_query() -> None:
    _core, plan = _plan("Le CSE est informé de la situation actuelle.")

    assert all(
        "documentary-history" not in rule
        for issue in plan.issues
        for rule in issue.created_from_rules
    )


def test_explicit_cssct_history_question_targets_only_cssct_minutes() -> None:
    _core, plan = _plan(
        "Retrouve dans les anciens PV CSSCT ce qui a été traité sur les EPI."
    )

    assert SourceFamily.CSSCT_MINUTES in {
        target.source_family for target in plan.targets
    }
    assert any(
        query.document_types == ("CSSCT_MINUTES",)
        for query in plan.queries
    )


def test_explicit_cse_history_question_reaches_selected_public_evidence(
    tmp_path,
    monkeypatch,
) -> None:
    root = corpus(tmp_path)
    core, _plan_result = _plan(CSE_HISTORY_QUESTION)
    monkeypatch.setenv("NEXUS_SOURCE_EXECUTION_COORDINATOR_ENABLED", "true")
    runtime_config = SourceExecutionRuntimeConfig(
        enabled=True,
        allow_network=False,
        cse_processed_root=root,
    )
    integration = RetrievalToResponseIntegration(
        RetrievalToResponseConfig(enabled=True),
        runtime=SourceExecutionRuntime(runtime_config),
    )

    result = integration.integrate(core)

    assert result.called is True
    assert result.fallback_code is None
    assert result.summary is not None
    assert result.summary.live_calls_attempted == 0
    assert all(event.network_call_executed is False for event in result.summary.events)
    assert result.summary.events[0].status is RetrievalStatus.LOCAL_DOCUMENT
    assert result.public_minutes
    assert any("horaires" in item["excerpt"].lower() for item in result.public_minutes)
    assert all(
        "ne constitue pas une norme" in item["legal_value"].lower()
        for item in result.public_minutes
    )
