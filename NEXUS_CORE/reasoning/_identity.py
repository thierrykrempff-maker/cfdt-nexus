"""Deterministic identifiers derived exclusively from technical references."""

from __future__ import annotations

from hashlib import sha256

from ..identifiers import EntityId


def stable_reasoning_id(prefix: str, parts: tuple[str, ...]) -> EntityId:
    payload = "\x1f".join((prefix,) + tuple(sorted(parts)))
    digest = sha256(payload.encode("utf-8")).hexdigest()[:24]
    return EntityId(f"{prefix}-{digest}")
