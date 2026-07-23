"""Stable pseudonymous identifiers for CSE adaptation artefacts."""

from __future__ import annotations

from hashlib import sha256


def stable_cse_id(prefix: str, *parts: str) -> str:
    payload = "\x1f".join((prefix,) + parts).encode("utf-8")
    digest = sha256(payload).hexdigest()[:24]
    grouped = "x".join(digest[index : index + 4] for index in range(0, len(digest), 4))
    return f"{prefix}-{grouped}"
