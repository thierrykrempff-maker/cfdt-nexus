"""Explicit feature configuration for the progressive Runtime bridge."""

from __future__ import annotations

from dataclasses import dataclass
import os
from collections.abc import Mapping
from pathlib import Path


CORE_RUNTIME_ENV = "NEXUS_CORE_RUNTIME_ENABLED"
CONNECTOR_RUNTIME_ENV = "NEXUS_CONNECTOR_RUNTIME_ENABLED"
CSE_MEMORY_RUNTIME_ENV = "NEXUS_CSE_MEMORY_RUNTIME_ENABLED"
CSE_MEMORY_ROOT_ENV = "NEXUS_CSE_MEMORY_PROCESSED_ROOT"
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"", "0", "false", "no", "off"})


@dataclass(frozen=True, slots=True)
class RuntimeIntegrationConfig:
    """Feature switch; disabled is the safe and backward-compatible default."""

    enabled: bool = False

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "RuntimeIntegrationConfig":
        source = os.environ if environ is None else environ
        raw = str(source.get(CORE_RUNTIME_ENV, "")).strip().lower()
        if raw in _TRUE_VALUES:
            return cls(True)
        if raw in _FALSE_VALUES:
            return cls(False)
        return cls(False)


@dataclass(frozen=True, slots=True)
class RuntimeConnectorConfig:
    """Independent switch for adapting connector results already returned by the router."""

    enabled: bool = False

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "RuntimeConnectorConfig":
        source = os.environ if environ is None else environ
        raw = str(source.get(CONNECTOR_RUNTIME_ENV, "")).strip().lower()
        if raw in _TRUE_VALUES:
            return cls(True)
        return cls(False)


@dataclass(frozen=True, slots=True)
class RuntimeCSEMemoryConfig:
    """Read-only access configuration for the existing LOT 1D chunk outputs."""

    enabled: bool = False
    processed_root: Path | None = None
    max_documents: int = 5
    max_chunks: int = 8

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        default_root: Path | None = None,
    ) -> "RuntimeCSEMemoryConfig":
        source = os.environ if environ is None else environ
        enabled = str(source.get(CSE_MEMORY_RUNTIME_ENV, "")).strip().lower() in _TRUE_VALUES
        configured = str(source.get(CSE_MEMORY_ROOT_ENV, "")).strip()
        root = Path(configured) if configured else default_root
        return cls(enabled, root)

    def __post_init__(self) -> None:
        if self.max_documents < 1 or self.max_chunks < 1:
            raise ValueError("CSE Memory limits must be positive")
