"""Public API for the domain-neutral Nexus orchestration framework."""

from .contracts import ExecutableEngine, ExecutionPlannerProtocol, ExecutionReporter
from .executor import PipelineExecutor
from .models import (
    EngineCapability,
    EngineDescriptor,
    ExecutionContext,
    ExecutionDiagnostics,
    ExecutionMetadata,
    ExecutionPlan,
    ExecutionReport,
    ExecutionResult,
    ExecutionStage,
    ExecutionStatus,
    ExecutionSummary,
)
from .planner import ExecutionPlanner
from .registry import EngineRegistry
from .report import ExecutionReportBuilder, JsonExecutionReporter

__all__ = [
    "EngineCapability",
    "EngineDescriptor",
    "EngineRegistry",
    "ExecutableEngine",
    "ExecutionContext",
    "ExecutionDiagnostics",
    "ExecutionMetadata",
    "ExecutionPlan",
    "ExecutionPlanner",
    "ExecutionPlannerProtocol",
    "ExecutionReport",
    "ExecutionReportBuilder",
    "ExecutionReporter",
    "ExecutionResult",
    "ExecutionStage",
    "ExecutionStatus",
    "ExecutionSummary",
    "JsonExecutionReporter",
    "PipelineExecutor",
]
