"""Minimal aggregation of technical results; expert reasoning stays untouched."""

from __future__ import annotations

from .models import AggregatedSummary, ExpertExecutionResult, OrchestrationError, OrchestrationStatus


def aggregate_results(
    executions: tuple[ExpertExecutionResult, ...], selection_errors: tuple[OrchestrationError, ...]
) -> tuple[tuple, tuple[OrchestrationError, ...], AggregatedSummary, OrchestrationStatus]:
    reports = tuple(item.report for item in executions if item.succeeded and item.report is not None)
    errors = selection_errors + tuple(item.error for item in executions if item.error is not None)
    attempted = tuple(item.expert_id for item in executions if item.attempted)
    successes = len(reports)
    failures = len(errors)
    summary = AggregatedSummary(attempted, successes, failures)
    if successes and not failures:
        status = OrchestrationStatus.SUCCESS
    elif successes:
        status = OrchestrationStatus.PARTIAL_SUCCESS
    elif not executions:
        status = OrchestrationStatus.NO_EXPERT_AVAILABLE
    else:
        status = OrchestrationStatus.FAILED
    return reports, errors, summary, status
