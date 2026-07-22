"""Stable pseudonymous identifiers for retirement adaptation artefacts."""

from __future__ import annotations

from hashlib import sha256


def stable_retirement_id(prefix: str, *parts: str) -> str:
    """Return a deterministic technical identifier without exposing source values."""

    payload = "\x1f".join((prefix,) + parts).encode("utf-8")
    digest = sha256(payload).hexdigest()[:24]
    safe_digest = "x".join(
        digest[index : index + 4] for index in range(0, len(digest), 4)
    )
    return f"{prefix}-{safe_digest}"
