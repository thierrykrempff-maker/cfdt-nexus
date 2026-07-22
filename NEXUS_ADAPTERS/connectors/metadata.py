"""Safe structured metadata conversion for connector snapshots."""

from __future__ import annotations

from NEXUS_CORE import DataSensitivity, MetadataEntry, RedactionStatus

from .models import MetadataItems


class ConnectorMetadataMapper:
    def map(self, values: MetadataItems) -> tuple[MetadataEntry, ...]:
        return tuple(self.entry(key, value) for key, value in values)

    @staticmethod
    def entry(key: str, value, *, sensitive: bool = False) -> MetadataEntry:
        normalized = "".join(character if character.isalnum() else "_" for character in key)
        normalized = normalized.strip("_") or "connector_metadata"
        return MetadataEntry(
            normalized,
            value,
            DataSensitivity.SENSITIVE if sensitive else DataSensitivity.NON_SENSITIVE,
            RedactionStatus.REDACTED if sensitive else RedactionStatus.NOT_REQUIRED,
        )
