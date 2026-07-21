"""Metadata-only CARSAT document synchronization with no transport."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from automation.official_knowledge.document_registry import (
    ChangeKind,
    DocumentRecord,
    DocumentRegistry,
    DocumentStatus,
    stable_document_id,
)

from .carsat_metadata import CARSAT_CONNECTOR_NAME, CarsatMetadata, CarsatMetadataRefusal, canonicalize_carsat_url


class CarsatSyncEventType(str, Enum):
    NEW = "NEW"
    UPDATED = "UPDATED"
    REMOVED = "REMOVED"
    REDIRECTED = "REDIRECTED"
    UNCHANGED = "UNCHANGED"


@dataclass(frozen=True)
class CarsatDocumentSnapshot:
    canonical_url: str
    title: str
    publication_date: str | None
    category: str
    family: str
    document_type: str
    provenance: str
    language: str
    status: str

    @classmethod
    def from_record(cls, record: DocumentRecord) -> "CarsatDocumentSnapshot":
        return cls(
            canonical_url=record.canonical_url,
            title=record.title,
            publication_date=record.publication_date,
            category=record.category,
            family=record.family,
            document_type=record.document_type,
            provenance=record.provenance,
            language=record.language,
            status=record.status.value,
        )


@dataclass(frozen=True)
class CarsatSyncEvent:
    document_id: str
    connector_name: str
    event_type: CarsatSyncEventType
    detected_at: str
    previous_snapshot: CarsatDocumentSnapshot | None
    new_snapshot: CarsatDocumentSnapshot | None

    def __post_init__(self) -> None:
        if self.connector_name != CARSAT_CONNECTOR_NAME:
            raise ValueError("invalid CARSAT synchronization event connector")
        _validate_date(self.detected_at)


@dataclass(frozen=True)
class CarsatRedirect:
    previous_url: str
    canonical_url: str

    def __post_init__(self) -> None:
        previous = canonicalize_carsat_url(self.previous_url)
        current = canonicalize_carsat_url(self.canonical_url)
        if previous == current:
            raise CarsatMetadataRefusal("INVALID_REDIRECT", "Redirect URLs must differ.")
        object.__setattr__(self, "previous_url", previous)
        object.__setattr__(self, "canonical_url", current)


class CarsatDocumentSync:
    """Compare injected CARSAT metadata through public registry operations only."""

    def __init__(self, registry: DocumentRegistry) -> None:
        if registry is None:
            raise CarsatMetadataRefusal("REGISTRY_NOT_CONFIGURED", "Document Registry must be explicitly injected.")
        self._registry = registry

    def compare_and_sync(
        self,
        metadata: tuple[CarsatMetadata, ...],
        *,
        detected_at: str,
        redirects: tuple[CarsatRedirect, ...] = (),
    ) -> tuple[CarsatSyncEvent, ...]:
        _validate_date(detected_at)
        if not isinstance(metadata, tuple) or any(not isinstance(item, CarsatMetadata) for item in metadata):
            raise CarsatMetadataRefusal("INVALID_SYNC_BATCH", "CARSAT metadata must be an immutable tuple.")
        if not isinstance(redirects, tuple) or any(not isinstance(item, CarsatRedirect) for item in redirects):
            raise CarsatMetadataRefusal("INVALID_REDIRECT_BATCH", "Redirects must be an immutable tuple.")
        incoming = _unique_by_url(metadata)
        known = self._registry.find_by_connector(CARSAT_CONNECTOR_NAME)
        known_by_url = {item.canonical_url: item for item in known}
        redirect_by_new = _validate_redirects(redirects, known_by_url, incoming)
        processed: set[str] = set()
        events: list[CarsatSyncEvent] = []

        for canonical_url, item in sorted(incoming.items()):
            redirect = redirect_by_new.get(canonical_url)
            previous = known_by_url.get(redirect.previous_url) if redirect else known_by_url.get(canonical_url)
            if previous is None:
                record = _to_record(item, detected_at, document_id=stable_document_id(CARSAT_CONNECTOR_NAME, canonical_url))
                change = self._registry.register_document(record)
            else:
                record = _to_record(
                    item,
                    detected_at,
                    document_id=previous.document_id,
                    first_seen=previous.first_seen,
                    previous_status=previous.status,
                    last_modified_metadata=previous.last_modified_metadata,
                )
                change = self._registry.update_document(record)
                processed.add(previous.document_id)
            processed.add(change.document_id)
            events.append(_event_from_change(change, detected_at))

        for previous in sorted(known, key=lambda item: item.document_id):
            if previous.document_id in processed or previous.status is DocumentStatus.REMOVED:
                continue
            events.append(_event_from_change(self._registry.mark_removed(previous.document_id, checked_on=detected_at), detected_at))
        return tuple(sorted(events, key=lambda event: (event.document_id, event.event_type.value)))


def _unique_by_url(metadata: tuple[CarsatMetadata, ...]) -> dict[str, CarsatMetadata]:
    result: dict[str, CarsatMetadata] = {}
    for item in metadata:
        if item.canonical_url in result:
            raise CarsatMetadataRefusal("DUPLICATE_DOCUMENT", "Duplicate CARSAT metadata identity.")
        result[item.canonical_url] = item
    return result


def _validate_redirects(
    redirects: tuple[CarsatRedirect, ...],
    known_by_url: dict[str, DocumentRecord],
    incoming: dict[str, CarsatMetadata],
) -> dict[str, CarsatRedirect]:
    result: dict[str, CarsatRedirect] = {}
    previous_urls: set[str] = set()
    for redirect in redirects:
        if redirect.previous_url in previous_urls or redirect.canonical_url in result:
            raise CarsatMetadataRefusal("DUPLICATE_REDIRECT", "Duplicate redirect declaration.")
        if redirect.previous_url not in known_by_url:
            raise CarsatMetadataRefusal("UNKNOWN_REDIRECT_SOURCE", "Redirect source is absent from the registry.")
        if redirect.canonical_url not in incoming:
            raise CarsatMetadataRefusal("MISSING_REDIRECT_TARGET", "Redirect target metadata is required.")
        previous_urls.add(redirect.previous_url)
        result[redirect.canonical_url] = redirect
    return result


def _to_record(
    item: CarsatMetadata,
    detected_at: str,
    *,
    document_id: str,
    first_seen: str | None = None,
    previous_status: DocumentStatus = DocumentStatus.ACTIVE,
    last_modified_metadata: str | None = None,
) -> DocumentRecord:
    return DocumentRecord(
        document_id=document_id,
        connector_name=CARSAT_CONNECTOR_NAME,
        canonical_url=item.canonical_url,
        title=item.title,
        category=item.category,
        family=item.family,
        document_type=item.document_type,
        publication_date=item.publication_date,
        first_seen=first_seen or detected_at,
        last_checked=detected_at,
        last_modified_metadata=last_modified_metadata or detected_at,
        language=item.language,
        provenance=item.provenance,
        status=previous_status,
    )


def _event_from_change(change, detected_at: str) -> CarsatSyncEvent:
    event_type = {
        ChangeKind.NEW: CarsatSyncEventType.NEW,
        ChangeKind.UNCHANGED: CarsatSyncEventType.UNCHANGED,
        ChangeKind.REMOVED: CarsatSyncEventType.REMOVED,
        ChangeKind.REDIRECTED: CarsatSyncEventType.REDIRECTED,
    }.get(change.kind, CarsatSyncEventType.UPDATED)
    return CarsatSyncEvent(
        document_id=change.document_id,
        connector_name=CARSAT_CONNECTOR_NAME,
        event_type=event_type,
        detected_at=detected_at,
        previous_snapshot=CarsatDocumentSnapshot.from_record(change.previous) if change.previous else None,
        new_snapshot=CarsatDocumentSnapshot.from_record(change.current) if change.current else None,
    )


def _validate_date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise CarsatMetadataRefusal("INVALID_DETECTION_DATE", "Detection date must use ISO YYYY-MM-DD format.") from exc
