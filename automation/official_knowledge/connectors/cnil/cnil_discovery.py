"""Bounded offline discovery over explicitly injected CNIL metadata."""

from __future__ import annotations

from dataclasses import dataclass

from .cnil_metadata import (
    CNIL_PROVENANCE,
    CnilMetadata,
    CnilMetadataRefusal,
    CnilTaxonomy,
    canonicalize_cnil_url,
    validate_cnil_mime_type,
)


DEFAULT_DISCOVERY_LIMIT = 50
MAX_DISCOVERY_LIMIT = 100


@dataclass(frozen=True)
class CnilDiscoveryEntry:
    url: str
    title: str
    publication_date: str | None
    category: CnilTaxonomy | str
    family: CnilTaxonomy | str
    document_type: CnilTaxonomy | str
    mime_type: str
    discovered_at: str
    provenance: str = CNIL_PROVENANCE
    language: str = "fr"


def discover_metadata(
    entries: tuple[CnilDiscoveryEntry, ...],
    *,
    enabled: bool,
    limit: int = DEFAULT_DISCOVERY_LIMIT,
) -> tuple[CnilMetadata, ...]:
    """Validate an immutable batch without transport, scraping or side effects."""

    if not isinstance(enabled, bool):
        raise TypeError("enabled must be a boolean")
    if not enabled:
        raise CnilMetadataRefusal("CONNECTOR_DISABLED", "CNIL metadata discovery is disabled.")
    if not isinstance(entries, tuple):
        raise CnilMetadataRefusal("INVALID_BATCH", "Discovery entries must be a tuple.")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_DISCOVERY_LIMIT:
        raise CnilMetadataRefusal("INVALID_LIMIT", "Discovery limit must be between 1 and 100.")
    if len(entries) > limit:
        raise CnilMetadataRefusal("LIMIT_EXCEEDED", "Discovery limit exceeded.")
    if any(not isinstance(entry, CnilDiscoveryEntry) for entry in entries):
        raise CnilMetadataRefusal("INVALID_ENTRY", "Unexpected discovery entry.")

    discovered: list[CnilMetadata] = []
    seen: set[str] = set()
    for entry in entries:
        canonical_url = canonicalize_cnil_url(entry.url)
        validate_cnil_mime_type(entry.mime_type)
        if canonical_url in seen:
            raise CnilMetadataRefusal("DUPLICATE_URL", "Duplicate canonical URL.")
        seen.add(canonical_url)
        discovered.append(CnilMetadata(
            canonical_url=canonical_url,
            title=entry.title,
            publication_date=entry.publication_date,
            category=entry.category,
            family=entry.family,
            document_type=entry.document_type,
            provenance=entry.provenance,
            language=entry.language,
            discovered_at=entry.discovered_at,
        ))
    return tuple(sorted(discovered, key=lambda item: item.canonical_url))
