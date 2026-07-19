"""Metadata-only INRS document synchronization with no transport."""

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

from .inrs_metadata import (
    INRS_CONNECTOR_NAME,
    InrsMetadata,
    InrsMetadataRefusal,
    canonicalize_inrs_url,
)


class InrsSyncEventType(str, Enum):
    NEW = "NEW"
    UPDATED = "UPDATED"
    REMOVED = "REMOVED"
    REDIRECTED = "REDIRECTED"
    UNCHANGED = "UNCHANGED"


@dataclass(frozen=True)
class InrsDocumentSnapshot:
    """Content-free metadata snapshot carried by a synchronization event."""

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
    def from_record(cls, record: DocumentRecord) -> "InrsDocumentSnapshot":
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
class InrsSyncEvent:
    document_id: str
    connector_name: str
    event_type: InrsSyncEventType
    detected_at: str
    previous_snapshot: InrsDocumentSnapshot | None
    new_snapshot: InrsDocumentSnapshot | None

    def __post_init__(self) -> None:
        if self.connector_name != INRS_CONNECTOR_NAME:
            raise ValueError("invalid INRS synchronization event connector")
        _validate_iso_date(self.detected_at)


@dataclass(frozen=True)
class InrsRedirect:
    previous_url: str
    canonical_url: str

    def __post_init__(self) -> None:
        previous = canonicalize_inrs_url(self.previous_url)
        current = canonicalize_inrs_url(self.canonical_url)
        if previous == current:
            raise InrsMetadataRefusal("INVALID_REDIRECT", "Redirect URLs must differ.")
        object.__setattr__(self, "previous_url", previous)
        object.__setattr__(self, "canonical_url", current)


class InrsDocumentSync:
    """Compare injected INRS metadata with an explicitly injected registry."""

    def __init__(self, registry: DocumentRegistry) -> None:
        if registry is None:
            raise InrsMetadataRefusal("REGISTRY_NOT_CONFIGURED", "Document Registry must be explicitly injected.")
        self._registry = registry

    def compare_and_sync(
        self,
        metadata: tuple[InrsMetadata, ...],
        *,
        detected_at: str,
        redirects: tuple[InrsRedirect, ...] = (),
    ) -> tuple[InrsSyncEvent, ...]:
        _validate_iso_date(detected_at)
        if not isinstance(metadata, tuple) or any(not isinstance(item, InrsMetadata) for item in metadata):
            raise InrsMetadataRefusal("INVALID_SYNC_BATCH", "INRS metadata must be an immutable tuple.")
        if not isinstance(redirects, tuple) or any(not isinstance(item, InrsRedirect) for item in redirects):
            raise InrsMetadataRefusal("INVALID_REDIRECT_BATCH", "Redirects must be an immutable tuple.")

        incoming = _unique_by_url(metadata)
        known = self._registry.find_by_connector(INRS_CONNECTOR_NAME)
        known_by_url = {item.canonical_url: item for item in known}
        redirect_by_new = _validate_redirects(redirects, known_by_url, incoming)
        processed: set[str] = set()
        events: list[InrsSyncEvent] = []

        for canonical_url, item in sorted(incoming.items()):
            redirect = redirect_by_new.get(canonical_url)
            previous = known_by_url.get(redirect.previous_url) if redirect else known_by_url.get(canonical_url)
            if previous is None:
                document_id = stable_document_id(INRS_CONNECTOR_NAME, canonical_url)
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


def _unique_by_url(metadata: tuple[InrsMetadata, ...]) -> dict[str, InrsMetadata]:
    result: dict[str, InrsMetadata] = {}
    document_ids: set[str] = set()
    for item in metadata:
        if item.canonical_url in result or item.document_id in document_ids:
            raise InrsMetadataRefusal("DUPLICATE_DOCUMENT", "Duplicate INRS metadata identity.")
        result[item.canonical_url] = item
        document_ids.add(item.document_id)
    return result


def _validate_redirects(
    redirects: tuple[InrsRedirect, ...],
    known_by_url: dict[str, DocumentRecord],
    incoming: dict[str, InrsMetadata],
) -> dict[str, InrsRedirect]:
    result: dict[str, InrsRedirect] = {}
    previous_urls: set[str] = set()
    for redirect in redirects:
        if redirect.previous_url in previous_urls or redirect.canonical_url in result:
            raise InrsMetadataRefusal("DUPLICATE_REDIRECT", "Duplicate redirect declaration.")
        if redirect.previous_url not in known_by_url:
            raise InrsMetadataRefusal("UNKNOWN_REDIRECT_SOURCE", "Redirect source is absent from the registry.")
        if redirect.canonical_url not in incoming:
            raise InrsMetadataRefusal("MISSING_REDIRECT_TARGET", "Redirect target metadata is required.")
        previous_urls.add(redirect.previous_url)
        result[redirect.canonical_url] = redirect
    return result


def _to_record(
    item: InrsMetadata,
    detected_at: str,
    *,
    document_id: str,
    first_seen: str | None = None,
    previous_status: DocumentStatus = DocumentStatus.ACTIVE,
    last_modified_metadata: str | None = None,
) -> DocumentRecord:
    return DocumentRecord(
        document_id=document_id,
        connector_name=INRS_CONNECTOR_NAME,
        canonical_url=item.canonical_url,
        title=item.title,
        category=item.category,
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


def _event_from_change(change, detected_at: str) -> InrsSyncEvent:
    event_type = {
        ChangeKind.NEW: InrsSyncEventType.NEW,
        ChangeKind.UNCHANGED: InrsSyncEventType.UNCHANGED,
        ChangeKind.REMOVED: InrsSyncEventType.REMOVED,
        ChangeKind.REDIRECTED: InrsSyncEventType.REDIRECTED,
    }.get(change.kind, InrsSyncEventType.UPDATED)
    return InrsSyncEvent(
        document_id=change.document_id,
        connector_name=INRS_CONNECTOR_NAME,
        event_type=event_type,
        detected_at=detected_at,
        previous_snapshot=InrsDocumentSnapshot.from_record(change.previous) if change.previous else None,
        new_snapshot=InrsDocumentSnapshot.from_record(change.current) if change.current else None,
    )


def _validate_iso_date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise InrsMetadataRefusal("INVALID_DETECTION_DATE", "Detection date must use ISO YYYY-MM-DD format.") from exc
