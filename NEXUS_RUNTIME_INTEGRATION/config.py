"""Explicit feature configuration for the progressive Runtime bridge."""

from __future__ import annotations

from dataclasses import dataclass
import os
from collections.abc import Mapping


CORE_RUNTIME_ENV = "NEXUS_CORE_RUNTIME_ENABLED"
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
