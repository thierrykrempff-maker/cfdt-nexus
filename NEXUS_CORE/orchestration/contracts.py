"""Public Protocols for engines, planners and orchestration reporters."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from ..identifiers import EntityId
from .models import (
    EngineCapability,
    EngineDescriptor,
    ExecutionContext,
    ExecutionPlan,
    ExecutionReport,
    ExecutionResult,
)


@runtime_checkable
class ExecutableEngine(Protocol):
    def execute(self, context: ExecutionContext) -> ExecutionResult: ...


@runtime_checkable
class ExecutionReporter(Protocol):
    def render(self, report: ExecutionReport) -> str: ...


@runtime_checkable
class ExecutionPlannerProtocol(Protocol):
    def plan(
        self,
        plan_id: EntityId,
        registry: "EngineRegistryProtocol",
        requested_capabilities: tuple[EngineCapability, ...],
        created_at: datetime,
    ) -> ExecutionPlan: ...


class EngineRegistryProtocol(Protocol):
    def list(self) -> tuple[EngineDescriptor, ...]: ...
