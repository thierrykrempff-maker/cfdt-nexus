"""Technical execution report construction and deterministic JSON export."""

from __future__ import annotations

from datetime import datetime

from ..identifiers import EntityId
from ..serialization import to_json
from .models import (
    ExecutionDiagnostics,
    ExecutionMetadata,
    ExecutionPlan,
    ExecutionReport,
    ExecutionResult,
    ExecutionStatus,
    ExecutionSummary,
)


class ExecutionReportBuilder:
    def build(
        self,
        report_id: EntityId,
        plan: ExecutionPlan,
        execution_id: EntityId,
        results: tuple[ExecutionResult, ...],
        diagnostics: tuple[ExecutionDiagnostics, ...],
        started_at: datetime,
        completed_at: datetime,
    ) -> ExecutionReport:
        capabilities = tuple(
            sorted(
                {capability for result in results for capability in result.capabilities_used},
                key=lambda item: item.code,
            )
        )
        total_duration = sum(result.duration_ms for result in results)
        summary = ExecutionSummary(
            len(plan.stages),
            len(results),
            sum(result.status is ExecutionStatus.SUCCEEDED for result in results),
            sum(result.status is ExecutionStatus.FAILED for result in results),
            len(plan.skipped_engines),
            capabilities,
            total_duration,
        )
        metadata = ExecutionMetadata(
            execution_id,
            plan.plan_id,
            started_at,
            completed_at,
            total_duration,
        )
        return ExecutionReport(
            report_id,
            metadata,
            tuple(result.engine_id for result in results),
            plan.skipped_engines,
            results,
            diagnostics,
            summary,
        )


class JsonExecutionReporter:
    def render(self, report: ExecutionReport) -> str:
        return to_json(report)
