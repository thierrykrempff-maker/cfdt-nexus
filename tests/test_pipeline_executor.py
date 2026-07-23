"""Sequential execution, aggregation and fail-safe error handling."""

from datetime import datetime, timezone

from NEXUS_CORE import EntityId
from NEXUS_CORE.orchestration import (
    EngineCapability,
    EngineDescriptor,
    EngineRegistry,
    ExecutionContext,
    ExecutionPlanner,
    ExecutionResult,
    ExecutionStatus,
    PipelineExecutor,
)


START = datetime(2026, 7, 21, 16, 0, tzinfo=timezone.utc)
END = datetime(2026, 7, 21, 16, 0, 1, tzinfo=timezone.utc)
CAPABILITY = EngineCapability("GENERIC_EXECUTION")


class RecordingEngine:
    def __init__(self, identifier, calls, fail=False):
        self.identifier = identifier
        self.calls = calls
        self.fail = fail

    def execute(self, context):
        self.calls.append(self.identifier.value)
        if self.fail:
            raise RuntimeError("synthetic-sensitive-error-value")
        return ExecutionResult(
            EntityId(f"result-{self.identifier.value}"),
            self.identifier,
            ExecutionStatus.SUCCEEDED,
            (CAPABILITY,),
            (EntityId(f"output-{self.identifier.value}"),),
            5,
        )


def setup_registry(failing=()):
    calls = []
    registry = EngineRegistry()
    for name in ("engine-second", "engine-first"):
        identifier = EntityId(name)
        registry.register(
            EngineDescriptor(identifier, "GENERIC_ENGINE", (CAPABILITY,)),
            RecordingEngine(identifier, calls, name in failing),
        )
    return registry, calls


def execute(registry):
    plan = ExecutionPlanner().plan(
        EntityId("plan-executor"), registry, (CAPABILITY,), START
    )
    context = ExecutionContext(
        EntityId("execution-sequential"),
        plan.plan_id,
        plan.requested_capabilities,
        (EntityId("input-technical-reference"),),
        START,
    )
    return PipelineExecutor().execute(plan, registry, context, END)


def test_executor_runs_stages_sequentially_and_aggregates_references():
    registry, calls = setup_registry()
    report = execute(registry)
    assert calls == ["engine-first", "engine-second"]
    assert report.summary.executed_count == 2
    assert report.summary.succeeded_count == 2
    assert report.summary.total_duration_ms == 10
    assert all(result.output_references for result in report.results)


def test_executor_converts_error_to_safe_diagnostic_and_continues():
    registry, calls = setup_registry(("engine-first",))
    report = execute(registry)
    assert calls == ["engine-first", "engine-second"]
    assert report.summary.failed_count == 1
    assert report.summary.succeeded_count == 1
    failed = report.results[0]
    assert failed.status is ExecutionStatus.FAILED
    assert failed.diagnostics[0].code == "ENGINE_EXECUTION_FAILED"
    assert not hasattr(failed.diagnostics[0], "message")
    assert not hasattr(failed.diagnostics[0], "exception_value")


def test_report_contains_no_business_payload_or_decision():
    registry, _ = setup_registry()
    report = execute(registry)
    assert not hasattr(report, "business_result")
    assert not hasattr(report, "legal_decision")
    assert not hasattr(report, "recommendation")
