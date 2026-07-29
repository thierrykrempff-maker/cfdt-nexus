"""Single, read-only source for the CFDT Nexus product version."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"


def get_nexus_version() -> str:
    """Return the validated release version stored at the repository root."""

    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    parts = version.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise RuntimeError("VERSION must use semantic major.minor.patch syntax")
    return version


__all__ = ("VERSION_FILE", "get_nexus_version")
