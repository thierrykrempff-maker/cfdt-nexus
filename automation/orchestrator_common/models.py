"""Typed, immutable models for technical expert orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from automation.contracts import ExpertReport, ExpertRequest
from automation.expert_facades import FacadeStatus


def _freeze_metadata(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("metadata must be a mapping")
    return MappingProxyType(dict(value))


class ErrorPolicy(str, Enum):
    CONTINUE = "CONTINUE"
    STOP = "STOP"


class OrchestrationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    NO_EXPERT_AVAILABLE = "NO_EXPERT_AVAILABLE"
    FAILED = "FAILED"


@dataclass(frozen=True)
class OrchestrationError:
    code: str
    message: str
    stage: str
    expert_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("code", "message", "stage"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be a non-empty string")
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True)
class OrchestrationRequest:
    expert_request: ExpertRequest
    requested_experts: tuple[str, ...] | None = None
    allow_partial_experts: bool = False
    error_policy: ErrorPolicy = ErrorPolicy.CONTINUE
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.expert_request, ExpertRequest):
            raise TypeError("expert_request must be an ExpertRequest")
        if self.requested_experts is not None:
            values = tuple(self.requested_experts)
            if any(not isinstance(item, str) or not item.strip() for item in values):
                raise ValueError("requested_experts must contain non-empty strings")
            object.__setattr__(self, "requested_experts", values)
        if not isinstance(self.error_policy, ErrorPolicy):
            raise TypeError("error_policy must be an ErrorPolicy")
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True)
class ExpertExecutionResult:
    expert_id: str
    registry_status: FacadeStatus
    attempted: bool
    succeeded: bool
    report: ExpertReport | None = None
    error: OrchestrationError | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.expert_id:
            raise ValueError("expert_id must be non-empty")
        if not isinstance(self.registry_status, FacadeStatus):
            raise TypeError("registry_status must be a FacadeStatus")
        if self.succeeded and (not self.attempted or self.report is None or self.error is not None):
            raise ValueError("a successful execution requires an attempted report and no error")
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True)
class AggregatedSummary:
    executed_experts: tuple[str, ...]
    success_count: int
    failure_count: int


@dataclass(frozen=True)
class OrchestrationResult:
    request_id: str
    selected_experts: tuple[str, ...]
    execution_results: tuple[ExpertExecutionResult, ...]
    reports: tuple[ExpertReport, ...]
    errors: tuple[OrchestrationError, ...]
    summary: AggregatedSummary
    status: OrchestrationStatus
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))
