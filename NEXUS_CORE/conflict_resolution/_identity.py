"""Stable technical identifiers for conflict-resolution artefacts."""

from __future__ import annotations

from hashlib import sha256

from ..identifiers import EntityId


def stable_resolution_id(prefix: str, *parts: str) -> EntityId:
    """Return a deterministic pseudonymous identifier from technical codes."""

    payload = "\x1f".join((prefix,) + parts).encode("utf-8")
    digest = sha256(payload).hexdigest()[:24]
    privacy_safe_digest = "x".join(
        digest[index : index + 4] for index in range(0, len(digest), 4)
    )
    return EntityId(f"{prefix}-{privacy_safe_digest}")
