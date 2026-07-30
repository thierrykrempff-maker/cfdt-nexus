from __future__ import annotations

from dataclasses import replace

from NEXUS_RUNTIME_INTEGRATION import SourceExecutionRuntimeResult
from SYNDICAL_REASONING_ENGINE import (
    ConnectorExecutionSummary,
    ConnectorKind,
    ResearchPlan,
    RetrievalEvent,
    RetrievalStatus,
    RetrievedDocument,
)


def summary_for(
    plan: ResearchPlan,
    *,
    status: RetrievalStatus = RetrievalStatus.LOCAL_DOCUMENT,
    provider: str = "PV CSE/CSSCT",
    title: str = "CSE 2024-03-12",
    excerpt: str | None = (
        "La direction indique que le sujet des horaires sera présenté au CSE."
    ),
    sensitive: bool = False,
) -> ConnectorExecutionSummary:
    query = plan.queries[0]
    target = next(item for item in plan.targets if item.target_id == query.target_id)
    event = RetrievalEvent(
        event_id="event-synthetic",
        case_session_id=plan.case_session_id,
        plan_id=plan.plan_id,
        issue_id=query.issue_id,
        target_id=query.target_id,
        query_id=query.query_id,
        connector_id="synthetic-local",
        connector_name=provider,
        connector_kind=ConnectorKind.LOCAL_INDEX,
        source_family=target.source_family.value,
        status=status,
        started_at="2026-01-01T00:00:00+00:00",
        completed_at="2026-01-01T00:00:00+00:00",
        duration_ms=1,
        live_call_attempted=False,
        network_call_executed=False,
        cache_checked=False,
        cache_hit=False,
        fixture_used=False,
        metadata_only=status in {
            RetrievalStatus.METADATA_ONLY,
            RetrievalStatus.TITLE_ONLY,
        },
        query_text=query.query_text,
        normalized_query=query.query_text.casefold(),
        endpoint_domain=None,
        http_status=None,
        result_count=1,
        accepted_count=1,
        rejected_count=0,
        provenance=(("synthetic_test", "true"),),
    )
    document = RetrievedDocument(
        document_id="document-synthetic",
        event_id=event.event_id,
        source_family=target.source_family.value,
        provider=provider,
        title=title,
        public_reference="12 mars 2024, page 3",
        document_type="meeting_minutes",
        date="2024-03-12",
        page="3",
        normalized_excerpt=excerpt,
        provenance=(
            ("passage_nature", "INFORMATION"),
            ("legal_value", "contexte et chronologie"),
            ("proves", "Le sujet a été évoqué en réunion."),
            ("does_not_prove", "Le passage ne prouve pas une obligation juridique."),
            ("final_score", "0.91"),
        ),
        status=status,
        metadata_complete=True,
        sensitive=sensitive,
        establishment_scope="Sarralbe",
        temporal_scope="2024",
    )
    return ConnectorExecutionSummary(
        case_session_id=plan.case_session_id,
        plan_id=plan.plan_id,
        total_queries=len(plan.queries) + len(plan.blocked_queries),
        executed_queries=1,
        blocked_queries=len(plan.blocked_queries),
        skipped_queries=max(0, len(plan.queries) - 1),
        live_calls_attempted=0,
        live_calls_succeeded=0,
        live_calls_failed=0,
        cache_results=0,
        local_results=1 if status is RetrievalStatus.LOCAL_DOCUMENT else 0,
        fixture_results=0,
        metadata_only_results=1
        if status in {RetrievalStatus.METADATA_ONLY, RetrievalStatus.TITLE_ONLY}
        else 0,
        unavailable_connectors=(),
        unconfigured_connectors=(),
        unsupported_sources=(),
        events=(event,),
        documents=(document,),
    )


def empty_summary(plan: ResearchPlan) -> ConnectorExecutionSummary:
    return ConnectorExecutionSummary(
        case_session_id=plan.case_session_id,
        plan_id=plan.plan_id,
        total_queries=len(plan.queries) + len(plan.blocked_queries),
        executed_queries=0,
        blocked_queries=len(plan.blocked_queries),
        skipped_queries=0,
        live_calls_attempted=0,
        live_calls_succeeded=0,
        live_calls_failed=0,
        cache_results=0,
        local_results=0,
        fixture_results=0,
        metadata_only_results=0,
        unavailable_connectors=(),
        unconfigured_connectors=(),
        unsupported_sources=(),
        events=(),
        documents=(),
    )


class RecordingRuntime:
    def __init__(self, **summary_kwargs):
        self.calls = 0
        self.summary_kwargs = summary_kwargs

    def execute(self, plan: ResearchPlan) -> SourceExecutionRuntimeResult:
        self.calls += 1
        return SourceExecutionRuntimeResult(
            called=True,
            summary=(
                summary_for(plan, **self.summary_kwargs)
                if plan.queries
                else empty_summary(plan)
            ),
        )


def with_distinct_id(bundle, suffix: str):
    return replace(bundle, evidence_id=f"{bundle.evidence_id}-{suffix}")
