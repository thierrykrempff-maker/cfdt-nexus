"""Sequential execution of capability-based plans with fail-safe diagnostics."""

from __future__ import annotations

from datetime import datetime

from ._identity import stable_execution_id
from .models import (
    ExecutionContext,
    ExecutionDiagnostics,
    ExecutionPlan,
    ExecutionReport,
    ExecutionResult,
    ExecutionStatus,
)
from .registry import EngineRegistry
from .report import ExecutionReportBuilder


class PipelineExecutor:
    def __init__(self) -> None:
        self._reports = ExecutionReportBuilder()

    def execute(
        self,
        plan: ExecutionPlan,
        registry: EngineRegistry,
        context: ExecutionContext,
        completed_at: datetime,
    ) -> ExecutionReport:
        if context.plan_id != plan.plan_id:
            raise ValueError("execution context must reference the execution plan")
        results = []
        diagnostics = []
        for stage in plan.stages:
            engine = registry.get(stage.engine_id)
            if engine is None:
                result, diagnostic = self._failure(stage.engine_id, "ENGINE_NOT_REGISTERED")
                results.append(result)
                diagnostics.append(diagnostic)
                continue
            try:
                result = engine.execute(context)
                self._validate_result(stage.engine_id, stage.capabilities, result)
            except Exception:
                result, diagnostic = self._failure(stage.engine_id, "ENGINE_EXECUTION_FAILED")
            results.append(result)
            diagnostics.extend(result.diagnostics)
        return self._reports.build(
            stable_execution_id("execution-report", context.execution_id.value),
            plan,
            context.execution_id,
            tuple(results),
            tuple(diagnostics),
            context.created_at,
            completed_at,
        )

    @staticmethod
    def _validate_result(engine_id, capabilities, result) -> None:
        if not isinstance(result, ExecutionResult):
            raise TypeError("engine must return ExecutionResult")
        if result.engine_id != engine_id:
            raise ValueError("engine result identifier mismatch")
        if not set(result.capabilities_used).issubset(capabilities):
            raise ValueError("engine used an undeclared stage capability")

    @staticmethod
    def _failure(engine_id, code):
        diagnostic = ExecutionDiagnostics(
            code,
            "execution_error",
            "high",
            engine_reference=engine_id,
        )
        result = ExecutionResult(
            stable_execution_id("result", engine_id.value, code),
            engine_id,
            ExecutionStatus.FAILED,
            (),
            diagnostics=(diagnostic,),
        )
        return result, diagnostic
