"""Capability-only planning with no domain ordering or business priority."""

from __future__ import annotations

from datetime import datetime

from ..identifiers import EntityId
from ._identity import stable_execution_id
from .models import EngineCapability, ExecutionPlan, ExecutionStage
from .registry import EngineRegistry


class ExecutionPlanner:
    def plan(
        self,
        plan_id: EntityId,
        registry: EngineRegistry,
        requested_capabilities: tuple[EngineCapability, ...],
        created_at: datetime,
    ) -> ExecutionPlan:
        if not requested_capabilities:
            raise ValueError("at least one capability must be requested")
        requested = tuple(sorted(set(requested_capabilities), key=lambda item: item.code))
        selected = []
        skipped = []
        for descriptor in registry.list():
            supported = tuple(
                capability
                for capability in requested
                if capability in descriptor.capabilities
            )
            if descriptor.enabled and supported:
                selected.append((descriptor.engine_id, supported))
            else:
                skipped.append(descriptor.engine_id)
        stages = tuple(
            ExecutionStage(
                stable_execution_id("stage", plan_id.value, engine_id.value),
                sequence,
                engine_id,
                capabilities,
            )
            for sequence, (engine_id, capabilities) in enumerate(selected, start=1)
        )
        return ExecutionPlan(
            plan_id,
            requested,
            stages,
            tuple(skipped),
            created_at,
        )
