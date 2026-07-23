"""Capability planning has deterministic technical order and no domain priority."""

from datetime import datetime, timezone

from NEXUS_CORE import EntityId
from NEXUS_CORE.orchestration import (
    EngineCapability,
    EngineDescriptor,
    EngineRegistry,
    ExecutionContext,
    ExecutionPlan,
    ExecutionPlanner,
    ExecutionPlannerProtocol,
    ExecutionResult,
    ExecutionStatus,
)


NOW = datetime(2026, 7, 21, 16, 0, tzinfo=timezone.utc)
ALPHA = EngineCapability("ALPHA_CAPABILITY")
BETA = EngineCapability("BETA_CAPABILITY")


class Engine:
    def __init__(self, identifier):
        self.identifier = identifier

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        return ExecutionResult(
            EntityId(f"result-{self.identifier.value}"),
            self.identifier,
            ExecutionStatus.SUCCEEDED,
            (),
        )


def register(registry, identifier, capabilities, enabled=True):
    engine_id = EntityId(identifier)
    registry.register(
        EngineDescriptor(engine_id, "GENERIC_ENGINE", capabilities, enabled),
        Engine(engine_id),
    )


def test_planner_selects_by_capability_and_records_skipped_engines():
    registry = EngineRegistry()
    register(registry, "engine-beta", (BETA,))
    register(registry, "engine-alpha", (ALPHA,))
    register(registry, "engine-disabled", (ALPHA,), enabled=False)
    plan = ExecutionPlanner().plan(
        EntityId("plan-capability"), registry, (ALPHA,), NOW
    )
    assert isinstance(plan, ExecutionPlan)
    assert tuple(stage.engine_id.value for stage in plan.stages) == ("engine-alpha",)
    assert tuple(item.value for item in plan.skipped_engines) == (
        "engine-beta",
        "engine-disabled",
    )


def test_planning_is_deterministic_and_has_no_domain_order():
    registry = EngineRegistry()
    register(registry, "engine-zeta", (ALPHA, BETA))
    register(registry, "engine-alpha", (ALPHA, BETA))
    planner = ExecutionPlanner()
    first = planner.plan(EntityId("plan-stable"), registry, (BETA, ALPHA), NOW)
    second = planner.plan(EntityId("plan-stable"), registry, (ALPHA, BETA), NOW)
    assert first == second
    assert tuple(stage.engine_id.value for stage in first.stages) == (
        "engine-alpha",
        "engine-zeta",
    )
    assert isinstance(planner, ExecutionPlannerProtocol)


def test_stage_identifiers_are_stable_and_capability_based():
    registry = EngineRegistry()
    register(registry, "engine-stable", (ALPHA,))
    planner = ExecutionPlanner()
    first = planner.plan(EntityId("plan-identity"), registry, (ALPHA,), NOW)
    second = planner.plan(EntityId("plan-identity"), registry, (ALPHA,), NOW)
    assert first.stages[0].stage_id == second.stages[0].stage_id
    assert first.stages[0].capabilities == (ALPHA,)
