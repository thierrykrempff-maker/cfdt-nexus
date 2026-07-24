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
RETIREMENT_RUNTIME_ENV = "NEXUS_RETIREMENT_RUNTIME_ENABLED"
PROTECTION_SOCIALE_RUNTIME_ENV = "NEXUS_PROTECTION_SOCIALE_RUNTIME_ENABLED"
PROTECTION_SOCIALE_ROOT_ENV = "NEXUS_PROTECTION_SOCIALE_PROCESSED_ROOT"
OFFICIAL_CONNECTORS_RUNTIME_ENV = "NEXUS_OFFICIAL_CONNECTORS_RUNTIME_ENABLED"
SYNDICAL_REASONING_RUNTIME_ENV = "NEXUS_SYNDICAL_REASONING_RUNTIME_ENABLED"
EXPERT_PAIE_V2_RUNTIME_ENV = "NEXUS_EXPERT_PAIE_V2_RUNTIME_ENABLED"
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


@dataclass(frozen=True, slots=True)
class RuntimeRetirementConfig:
    """Independent, fail-safe switch for the Retirement Runtime bridge."""

    enabled: bool = False

    @classmethod
    def from_env(
        cls, environ: Mapping[str, str] | None = None
    ) -> "RuntimeRetirementConfig":
        source = os.environ if environ is None else environ
        enabled = str(source.get(RETIREMENT_RUNTIME_ENV, "")).strip().lower() in _TRUE_VALUES
        return cls(enabled)


@dataclass(frozen=True, slots=True)
class RuntimeProtectionSocialeConfig:
    """Read-only configuration for bounded Protection Sociale metadata lookup."""

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
    ) -> "RuntimeProtectionSocialeConfig":
        source = os.environ if environ is None else environ
        enabled = str(source.get(PROTECTION_SOCIALE_RUNTIME_ENV, "")).strip().lower() in _TRUE_VALUES
        configured = str(source.get(PROTECTION_SOCIALE_ROOT_ENV, "")).strip()
        root = Path(configured) if configured else default_root
        return cls(enabled, root)

    def __post_init__(self) -> None:
        if self.max_documents < 1 or self.max_chunks < 1:
            raise ValueError("Protection Sociale limits must be positive")


@dataclass(frozen=True, slots=True)
class RuntimeOfficialConnectorsConfig:
    """Independent switch for offline official-connector metadata discovery."""

    enabled: bool = False
    max_documents_per_connector: int = 50

    @classmethod
    def from_env(
        cls, environ: Mapping[str, str] | None = None
    ) -> "RuntimeOfficialConnectorsConfig":
        source = os.environ if environ is None else environ
        enabled = str(source.get(OFFICIAL_CONNECTORS_RUNTIME_ENV, "")).strip().lower() in _TRUE_VALUES
        return cls(enabled)

    def __post_init__(self) -> None:
        if not 1 <= self.max_documents_per_connector <= 100:
            raise ValueError("official connector limit must be between 1 and 100")


@dataclass(frozen=True, slots=True)
class RuntimeSyndicalReasoningConfig:
    """Independent, backward-compatible switch for syndical reasoning."""

    enabled: bool = False

    @classmethod
    def from_env(
        cls, environ: Mapping[str, str] | None = None
    ) -> "RuntimeSyndicalReasoningConfig":
        source = os.environ if environ is None else environ
        enabled = (
            str(source.get(SYNDICAL_REASONING_RUNTIME_ENV, "")).strip().lower()
            in _TRUE_VALUES
        )
        return cls(enabled)


@dataclass(frozen=True, slots=True)
class RuntimeExpertPaieV2Config:
    """Independent, fail-safe switch for Expert Paie V2."""

    enabled: bool = False

    @classmethod
    def from_env(
        cls, environ: Mapping[str, str] | None = None
    ) -> "RuntimeExpertPaieV2Config":
        source = os.environ if environ is None else environ
        enabled = (
            str(source.get(EXPERT_PAIE_V2_RUNTIME_ENV, "")).strip().lower()
            in _TRUE_VALUES
        )
        return cls(enabled)
