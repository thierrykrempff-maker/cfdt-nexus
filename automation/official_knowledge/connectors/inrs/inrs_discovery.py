"""Deterministic offline discovery over explicitly injected INRS metadata."""

from __future__ import annotations

from typing import Any, Mapping

from .inrs_metadata import InrsMetadata, InrsMetadataRefusal, metadata_from_mapping


DEFAULT_DISCOVERY_LIMIT = 50
MAX_DISCOVERY_LIMIT = 100


def discover_inrs_metadata(
    entries: tuple[Mapping[str, Any], ...],
    *,
    enabled: bool,
    limit: int = DEFAULT_DISCOVERY_LIMIT,
) -> tuple[InrsMetadata, ...]:
    """Normalize a bounded synthetic batch without transport or side effects."""

    if not isinstance(enabled, bool):
        raise TypeError("enabled must be a boolean")
    if not enabled:
        raise InrsMetadataRefusal("CONNECTOR_DISABLED", "INRS metadata discovery is disabled.")
    if not isinstance(entries, tuple):
        raise InrsMetadataRefusal("INVALID_BATCH", "Discovery entries must be a tuple.")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_DISCOVERY_LIMIT:
        raise InrsMetadataRefusal("INVALID_LIMIT", "Discovery limit must be between 1 and 100.")
    if len(entries) > limit:
        raise InrsMetadataRefusal("LIMIT_EXCEEDED", "Discovery limit exceeded.")

    documents: dict[str, InrsMetadata] = {}
    for entry in entries:
        document = metadata_from_mapping(entry)
        previous = documents.get(document.document_id)
        if previous is not None and previous != document:
            raise InrsMetadataRefusal("DUPLICATE_CONFLICT", "Conflicting metadata share one document identity.")
        documents[document.document_id] = document
    return tuple(sorted(documents.values(), key=lambda item: (item.canonical_url, item.document_id)))
