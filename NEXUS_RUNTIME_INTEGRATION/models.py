"""Safe immutable input, result and diagnostics for Runtime integration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any


class RuntimeMode(str, Enum):
    LEGACY = "legacy"
    CORE_V3 = "core_v3"
    CORE_V3_FALLBACK = "core_v3_fallback"


@dataclass(frozen=True, slots=True)
class RuntimeCoreIntegrationInput:
    answer: Mapping[str, Any]
    legal_payload: object
    payroll_payload: object
    historical_orchestration: Mapping[str, Any]
    connector_inputs: tuple[object, ...] = ()
    connector_runtime_enabled: bool = False
    connector_mapping_fallback_code: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.answer, Mapping):
            raise TypeError("answer must be a mapping")
        if not isinstance(self.historical_orchestration, Mapping):
            raise TypeError("historical_orchestration must be a mapping")
        if not isinstance(self.connector_inputs, tuple):
            raise TypeError("connector_inputs must be a tuple")


@dataclass(frozen=True, slots=True)
class RuntimeCoreIntegrationDiagnostics:
    core_enabled: bool
    legal_executed: bool = False
    payroll_executed: bool = False
    payroll_adapter_called: bool = False
    core_pipeline_called: bool = False
    common_orchestrator_called: bool = False
    evidence_count: int = 0
    finding_count: int = 0
    recommendation_count: int = 0
    connector_runtime_enabled: bool = False
    connector_adapter_called: bool = False
    connector_count: int = 0
    connector_snapshot_count: int = 0
    connector_evidence_count: int = 0
    connector_fallback_triggered: bool = False
    connector_fallback_code: str | None = None
    fallback_triggered: bool = False
    fallback_code: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "evidence_count", "finding_count", "recommendation_count", "connector_count",
            "connector_snapshot_count", "connector_evidence_count",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        for name in ("fallback_code", "connector_fallback_code"):
            code = getattr(self, name)
            if code is not None and (not code or not code.replace("_", "").isalnum()):
                raise ValueError(f"{name} must be a stable technical code")

    def to_dict(self) -> dict[str, Any]:
        return {
            "core_enabled": self.core_enabled,
            "legal_executed": self.legal_executed,
            "payroll_executed": self.payroll_executed,
            "payroll_adapter_called": self.payroll_adapter_called,
            "core_pipeline_called": self.core_pipeline_called,
            "common_orchestrator_called": self.common_orchestrator_called,
            "evidence_count": self.evidence_count,
            "finding_count": self.finding_count,
            "recommendation_count": self.recommendation_count,
            "connector_runtime_enabled": self.connector_runtime_enabled,
            "connector_adapter_called": self.connector_adapter_called,
            "connector_count": self.connector_count,
            "connector_snapshot_count": self.connector_snapshot_count,
            "connector_evidence_count": self.connector_evidence_count,
            "connector_fallback_triggered": self.connector_fallback_triggered,
            "connector_fallback_code": self.connector_fallback_code,
            "fallback_triggered": self.fallback_triggered,
            "fallback_code": self.fallback_code,
        }


@dataclass(frozen=True, slots=True)
class RuntimeCoreIntegrationResult:
    runtime_mode: RuntimeMode
    diagnostics: RuntimeCoreIntegrationDiagnostics
    core_status: str | None = None
    common_orchestrator_status: str | None = None
    selected_experts: tuple[str, ...] = ()
    report_items: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime_mode": self.runtime_mode.value,
            "diagnostics": self.diagnostics.to_dict(),
            "core_status": self.core_status,
            "common_orchestrator_status": self.common_orchestrator_status,
            "selected_experts": list(self.selected_experts),
            "report_items": list(self.report_items),
        }
