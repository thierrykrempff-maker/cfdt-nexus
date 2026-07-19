"""Metadata-only CNIL document synchronization with no transport."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from automation.official_knowledge.document_registry import (
    ChangeKind,
    DocumentRecord,
    DocumentRegistry,
    DocumentStatus,
    stable_document_id,
)

from .cnil_metadata import (
    CNIL_CONNECTOR_NAME,
    CnilMetadata,
    CnilMetadataRefusal,
    canonicalize_cnil_url,
)
from .cnil_platform import network_not_implemented


class CnilSyncEventType(StrEnum):
    NEW = "NEW"
    UPDATED = "UPDATED"
    REMOVED = "REMOVED"
    REDIRECTED = "REDIRECTED"
    UNCHANGED = "UNCHANGED"


@dataclass(frozen=True)
class CnilDocumentSnapshot:
    """Content-free value carried by synchronization events."""

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
    def from_record(cls, record: DocumentRecord) -> "CnilDocumentSnapshot":
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
class CnilSyncEvent:
    document_id: str
    connector_name: str
    event_type: CnilSyncEventType
    detected_at: str
    old_value: CnilDocumentSnapshot | None
    new_value: CnilDocumentSnapshot | None

    def __post_init__(self) -> None:
        if self.connector_name != CNIL_CONNECTOR_NAME:
            raise ValueError("invalid CNIL synchronization event connector")
        _validate_iso_date(self.detected_at)


@dataclass(frozen=True)
class CnilRedirect:
    previous_url: str
    canonical_url: str

    def __post_init__(self) -> None:
        previous = canonicalize_cnil_url(self.previous_url)
        current = canonicalize_cnil_url(self.canonical_url)
        if previous == current:
            raise CnilMetadataRefusal("INVALID_REDIRECT", "Redirect URLs must differ.")
        object.__setattr__(self, "previous_url", previous)
        object.__setattr__(self, "canonical_url", current)


class CnilDocumentSync:
    """Compare injected CNIL metadata with an explicitly injected registry."""

    def __init__(self, registry: DocumentRegistry) -> None:
        if registry is None:
            raise CnilMetadataRefusal("REGISTRY_NOT_CONFIGURED", "Document Registry must be explicitly injected.")
        self._registry = registry

    def compare_and_sync(
        self,
        metadata: tuple[CnilMetadata, ...],
        *,
        detected_at: str,
        redirects: tuple[CnilRedirect, ...] = (),
    ) -> tuple[CnilSyncEvent, ...]:
        _validate_iso_date(detected_at)
        if not isinstance(metadata, tuple) or any(not isinstance(item, CnilMetadata) for item in metadata):
            raise CnilMetadataRefusal("INVALID_SYNC_BATCH", "CNIL metadata must be an immutable tuple.")
        if not isinstance(redirects, tuple) or any(not isinstance(item, CnilRedirect) for item in redirects):
            raise CnilMetadataRefusal("INVALID_REDIRECT_BATCH", "Redirects must be an immutable tuple.")

        incoming = _unique_by_url(metadata)
        known = self._registry.find_by_connector(CNIL_CONNECTOR_NAME)
        known_by_url = {item.canonical_url: item for item in known}
        redirect_by_new = _validate_redirects(redirects, known_by_url, incoming)
        processed: set[str] = set()
        events: list[CnilSyncEvent] = []

        for canonical_url, item in sorted(incoming.items()):
            redirect = redirect_by_new.get(canonical_url)
            previous = known_by_url.get(redirect.previous_url) if redirect else known_by_url.get(canonical_url)
            if previous is None:
                document_id = stable_document_id(CNIL_CONNECTOR_NAME, canonical_url)
                record = _to_record(item, detected_at, document_id=document_id)
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
            change = self._registry.mark_removed(previous.document_id, checked_on=detected_at)
            events.append(_event_from_change(change, detected_at))

        return tuple(sorted(events, key=lambda event: (event.document_id, event.event_type.value)))


def _unique_by_url(metadata: tuple[CnilMetadata, ...]) -> dict[str, CnilMetadata]:
    result: dict[str, CnilMetadata] = {}
    for item in metadata:
        if item.canonical_url in result:
            raise CnilMetadataRefusal("DUPLICATE_URL", "Duplicate CNIL metadata URL.")
        result[item.canonical_url] = item
    return result


def _validate_redirects(
    redirects: tuple[CnilRedirect, ...],
    known_by_url: dict[str, DocumentRecord],
    incoming: dict[str, CnilMetadata],
) -> dict[str, CnilRedirect]:
    result: dict[str, CnilRedirect] = {}
    previous_urls: set[str] = set()
    for redirect in redirects:
        if redirect.previous_url in previous_urls or redirect.canonical_url in result:
            raise CnilMetadataRefusal("DUPLICATE_REDIRECT", "Duplicate redirect declaration.")
        if redirect.previous_url not in known_by_url:
            raise CnilMetadataRefusal("UNKNOWN_REDIRECT_SOURCE", "Redirect source is absent from the registry.")
        if redirect.canonical_url not in incoming:
            raise CnilMetadataRefusal("MISSING_REDIRECT_TARGET", "Redirect target metadata is required.")
        previous_urls.add(redirect.previous_url)
        result[redirect.canonical_url] = redirect
    return result


def _to_record(
    item: CnilMetadata,
    detected_at: str,
    *,
    document_id: str,
    first_seen: str | None = None,
    previous_status: DocumentStatus = DocumentStatus.ACTIVE,
    last_modified_metadata: str | None = None,
) -> DocumentRecord:
    return DocumentRecord(
        document_id=document_id,
        connector_name=CNIL_CONNECTOR_NAME,
        canonical_url=item.canonical_url,
        title=item.title,
        category=item.category.value,
        family=item.family.value,
        document_type=item.document_type.value,
        publication_date=item.publication_date,
        first_seen=first_seen or detected_at,
        last_checked=detected_at,
        last_modified_metadata=last_modified_metadata or detected_at,
        language=item.language,
        provenance=item.provenance,
        status=previous_status,
    )


def _event_from_change(change, detected_at: str) -> CnilSyncEvent:
    event_type = {
        ChangeKind.NEW: CnilSyncEventType.NEW,
        ChangeKind.UNCHANGED: CnilSyncEventType.UNCHANGED,
        ChangeKind.REMOVED: CnilSyncEventType.REMOVED,
        ChangeKind.REDIRECTED: CnilSyncEventType.REDIRECTED,
    }.get(change.kind, CnilSyncEventType.UPDATED)
    return CnilSyncEvent(
        document_id=change.document_id,
        connector_name=CNIL_CONNECTOR_NAME,
        event_type=event_type,
        detected_at=detected_at,
        old_value=CnilDocumentSnapshot.from_record(change.previous) if change.previous else None,
        new_value=CnilDocumentSnapshot.from_record(change.current) if change.current else None,
    )


def _validate_iso_date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise CnilMetadataRefusal("INVALID_DETECTION_DATE", "Detection date must use ISO YYYY-MM-DD format.") from exc


# Historical transport synchronization remains unavailable and fail-closed.
def synchronize(*_args,**_kwargs):raise network_not_implemented()
