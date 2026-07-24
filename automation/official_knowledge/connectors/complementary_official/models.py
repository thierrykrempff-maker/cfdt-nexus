"""Immutable configuration for complementary metadata-only sources."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ComplementaryConnectorSpec:
    connector_id: str
    display_name: str
    publisher: str
    official_domains: frozenset[str]
    authority: str
    tags: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.connector_id or not self.display_name or not self.publisher:
            raise ValueError("connector specification is incomplete")
        if not self.official_domains or any(
            not domain or domain != domain.lower() for domain in self.official_domains
        ):
            raise ValueError("official domains are required")
