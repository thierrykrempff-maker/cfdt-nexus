"""Offline, explicitly activable metadata discovery for DREETS LOT 3A."""

from __future__ import annotations

from dataclasses import dataclass
from .dreets_metadata import (
    DREETS_PROVENANCE,
    LOT_3A_DOCUMENT_POLICY,
    DreetsDocumentPolicy,
    DreetsMetadata,
    DreetsMetadataRefusal,
    canonicalize_public_url,
    validate_metadata_mime_type,
)


DEFAULT_DISCOVERY_QUOTA = 50
MAX_DISCOVERY_QUOTA = 100


@dataclass(frozen=True)
class DreetsDiscoveryItem:
    """Metadata-only input supplied by a separately controlled transport."""

    url: str
    title: str
    date: str | None
    category: str
    family: str
    document_type: str
    mime_type: str
    provenance: str = DREETS_PROVENANCE
    language: str = "fr"


class DreetsMetadataDiscovery:
    """Validate supplied public metadata; never fetch, cache or index content."""

    def __init__(self, *, activated: bool = False, quota: int = DEFAULT_DISCOVERY_QUOTA) -> None:
        if not isinstance(activated, bool):
            raise TypeError("activated must be a boolean")
        if not isinstance(quota, int) or isinstance(quota, bool) or not 1 <= quota <= MAX_DISCOVERY_QUOTA:
            raise ValueError("quota must be between 1 and 100")
        self.activated = activated
        self.quota = quota
        self.policy: DreetsDocumentPolicy = LOT_3A_DOCUMENT_POLICY

    def activate(self) -> "DreetsMetadataDiscovery":
        """Return an explicitly activated immutable-configuration service."""
        return type(self)(activated=True, quota=self.quota)

    def discover(self, items: tuple[DreetsDiscoveryItem, ...], *, discovered_on: str) -> tuple[DreetsMetadata, ...]:
        if not self.activated:
            raise DreetsMetadataRefusal("DISCOVERY_NOT_ACTIVATED", "Metadata discovery must be explicitly activated.")
        if not isinstance(items, tuple):
            raise DreetsMetadataRefusal("INVALID_DISCOVERY_BATCH", "Discovery batch must be a bounded tuple.")
        records = items
        if len(records) > self.quota:
            raise DreetsMetadataRefusal("QUOTA_EXCEEDED", "Metadata discovery quota exceeded.")
        if any(not isinstance(item, DreetsDiscoveryItem) for item in records):
            raise DreetsMetadataRefusal("INVALID_DISCOVERY_ITEM", "Unexpected discovery item.")
        discovered: list[DreetsMetadata] = []
        seen: set[str] = set()
        for item in records:
            canonical_url = canonicalize_public_url(item.url)
            validate_metadata_mime_type(item.mime_type)
            if canonical_url in seen:
                raise DreetsMetadataRefusal("DUPLICATE_URL", "Duplicate canonical URL.")
            seen.add(canonical_url)
            discovered.append(DreetsMetadata(
                canonical_url=canonical_url,
                title=item.title,
                date=item.date,
                category=item.category,
                family=item.family,
                document_type=item.document_type,
                provenance=item.provenance,
                language=item.language,
                discovered_on=discovered_on,
            ))
        return tuple(discovered)
