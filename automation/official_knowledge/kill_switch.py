"""Fail-closed environment switches."""
from __future__ import annotations
import os, re

def _enabled(name: str, environ=None) -> bool:
    value=(environ or os.environ).get(name)
    return value is not None and value.strip().casefold() in {"1","true","yes","on"}

def network_enabled(environ=None) -> bool: return _enabled("OFFICIAL_KNOWLEDGE_NETWORK_ENABLED",environ)
def source_enabled(source_id: str,environ=None) -> bool:
    key=re.sub(r"[^A-Z0-9]+","_",source_id.upper())
    return network_enabled(environ) and _enabled(f"OFFICIAL_KNOWLEDGE_SOURCE_{key}_ENABLED",environ)

def blocked_features(environ=None) -> dict[str,bool]:
    env=environ or os.environ
    return {name:not _enabled(f"OFFICIAL_KNOWLEDGE_{name.upper()}_ENABLED",env) for name in ("automatic_sync","downloads")}
