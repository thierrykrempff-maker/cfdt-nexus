"""Immutable, domain-neutral models for the Nexus orchestration framework."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..identifiers import EntityId


def _technical_code(value: str, label: str) -> None:
    if not value or not value.replace("_", "").isalnum():
        raise ValueError(f"{label} must be a stable technical code")


@dataclass(frozen=True, slots=True, order=True)
class EngineCapability:
    code: str

    def __post_init__(self) -> None:
        _technical_code(self.code, "capability")


@dataclass(frozen=True, slots=True)
class EngineDescriptor:
    engine_id: EntityId
    label_code: str
    capabilities: tuple[EngineCapability, ...]
    enabled: bool = True
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        _technical_code(self.label_code, "engine label")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise ValueError("engine capabilities must be unique")


@dataclass(frozen=True, slots=True)
class ExecutionStage:
    stage_id: EntityId
    sequence: int
    engine_id: EntityId
    capabilities: tuple[EngineCapability, ...]
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("execution stage sequence starts at one")
        if not self.capabilities:
            raise ValueError("execution stage requires at least one capability")


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    plan_id: EntityId
    requested_capabilities: tuple[EngineCapability, ...]
    stages: tuple[ExecutionStage, ...]
    skipped_engines: tuple[EntityId, ...]
    created_at: datetime
    schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    execution_id: EntityId
    plan_id: EntityId
    requested_capabilities: tuple[EngineCapability, ...]
    input_references: tuple[EntityId, ...]
    created_at: datetime
    schema_version: str = "1.0"


class ExecutionStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class ExecutionDiagnostics:
    code: str
    category: str
    severity: str
    engine_reference: EntityId | None = None
    technical_reference: EntityId | None = None
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        for value in (self.code, self.category, self.severity):
            _technical_code(value, "diagnostic field")


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    result_id: EntityId
    engine_id: EntityId
    status: ExecutionStatus
    capabilities_used: tuple[EngineCapability, ...]
    output_references: tuple[EntityId, ...] = ()
    duration_ms: int = 0
    diagnostics: tuple[ExecutionDiagnostics, ...] = ()
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.duration_ms < 0:
            raise ValueError("execution duration must be non-negative")
        if len(set(self.output_references)) != len(self.output_references):
            raise ValueError("output references must be unique")


@dataclass(frozen=True, slots=True)
class ExecutionMetadata:
    execution_id: EntityId
    plan_id: EntityId
    started_at: datetime
    completed_at: datetime
    duration_ms: int
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.completed_at < self.started_at:
            raise ValueError("execution completion cannot precede start")
        if self.duration_ms < 0:
            raise ValueError("execution duration must be non-negative")


@dataclass(frozen=True, slots=True)
class ExecutionSummary:
    planned_count: int
    executed_count: int
    succeeded_count: int
    failed_count: int
    skipped_count: int
    capabilities_used: tuple[EngineCapability, ...]
    total_duration_ms: int
    schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    report_id: EntityId
    metadata: ExecutionMetadata
    executed_engines: tuple[EntityId, ...]
    skipped_engines: tuple[EntityId, ...]
    results: tuple[ExecutionResult, ...]
    diagnostics: tuple[ExecutionDiagnostics, ...]
    summary: ExecutionSummary
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if hasattr(self, "business_result") or hasattr(self, "legal_decision"):
            raise ValueError("execution reports cannot expose domain decisions")
