"""Opt-in bridge from a LOT 2 ResearchPlan to the LOT 3 coordinator."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Mapping, Sequence

from SYNDICAL_REASONING_ENGINE import (
    ConnectorExecutionSummary,
    ConnectorExecutor,
    ResearchPlan,
    SourceExecutionCoordinator,
    build_default_executors,
)


ENV_ENABLED = "NEXUS_SOURCE_EXECUTION_COORDINATOR_ENABLED"


def _enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class SourceExecutionRuntimeConfig:
    enabled: bool = False
    allow_network: bool = False

    @classmethod
    def from_env(cls) -> "SourceExecutionRuntimeConfig":
        return cls(enabled=_enabled(os.environ.get(ENV_ENABLED)), allow_network=False)


@dataclass(frozen=True, slots=True)
class SourceExecutionRuntimeResult:
    called: bool
    summary: ConnectorExecutionSummary | None = None
    fallback_code: str | None = None


class SourceExecutionRuntime:
    """Reversible runtime seam; disabled means the historical engine is untouched."""

    def __init__(
        self,
        config: SourceExecutionRuntimeConfig | None = None,
        *,
        executors: Sequence[ConnectorExecutor] | None = None,
        catalogs: Mapping[str, Sequence[Mapping[str, object]]] | None = None,
    ) -> None:
        self._config = config or SourceExecutionRuntimeConfig.from_env()
        self._coordinator = SourceExecutionCoordinator(
            tuple(executors) if executors is not None else build_default_executors(catalogs=catalogs)
        )

    def execute(self, plan: ResearchPlan) -> SourceExecutionRuntimeResult:
        if not self._config.enabled:
            return SourceExecutionRuntimeResult(False)
        try:
            summary = self._coordinator.execute(
                plan, allow_network=self._config.allow_network
            )
        except Exception:
            return SourceExecutionRuntimeResult(
                True, fallback_code="SOURCE_EXECUTION_COORDINATOR_FAILED"
            )
        return SourceExecutionRuntimeResult(True, summary)


__all__ = (
    "ENV_ENABLED",
    "SourceExecutionRuntime",
    "SourceExecutionRuntimeConfig",
    "SourceExecutionRuntimeResult",
)
