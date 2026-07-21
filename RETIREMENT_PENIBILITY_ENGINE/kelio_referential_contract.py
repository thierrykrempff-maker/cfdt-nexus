"""Filesystem-independent public contract for Kelio counter lookup."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .kelio_referential_models import KelioCounterMetadata, KelioCounterResolution


@runtime_checkable
class KelioReferentialLookup(Protocol):
    def resolve_counter(self, counter_id: str) -> KelioCounterResolution: ...

    def is_known_counter(self, counter_id: str) -> bool: ...

    def get_counter_metadata(self, counter_id: str) -> KelioCounterMetadata | None: ...

    def list_supported_counter_ids(self) -> tuple[str, ...]: ...


__all__ = ("KelioReferentialLookup",)
