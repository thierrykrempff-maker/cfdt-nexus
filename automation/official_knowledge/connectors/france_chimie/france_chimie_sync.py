"""Offline metadata-only synchronization for France Chimie documents."""

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

from .france_chimie_metadata import (
    FRANCE_CHIMIE_CONNECTOR_NAME,
    FranceChimieMetadata,
    FranceChimieMetadataRefusal,
    canonicalize_france_chimie_url,
)


class FranceChimieSyncEventType(str, Enum):
    NEW = "NEW"
    UPDATED = "UPDATED"
    REMOVED = "REMOVED"
    REDIRECTED = "REDIRECTED"
    UNCHANGED = "UNCHANGED"


@dataclass(frozen=True)
class FranceChimieDocumentSnapshot:
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
    def from_record(cls, record: DocumentRecord) -> "FranceChimieDocumentSnapshot":
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
class FranceChimieSyncEvent:
    document_id: str
    connector_name: str
    event_type: FranceChimieSyncEventType
    detected_at: str
    previous_snapshot: FranceChimieDocumentSnapshot | None
    new_snapshot: FranceChimieDocumentSnapshot | None

    def __post_init__(self) -> None:
        if self.connector_name != FRANCE_CHIMIE_CONNECTOR_NAME:
            raise ValueError("invalid France Chimie synchronization event connector")
        if not isinstance(self.event_type, FranceChimieSyncEventType):
            raise TypeError("event_type must be a FranceChimieSyncEventType")
        _validate_date(self.detected_at)


@dataclass(frozen=True)
class FranceChimieRedirect:
    previous_url: str
    canonical_url: str

    def __post_init__(self) -> None:
        if not isinstance(self.previous_url, str) or not self.previous_url.startswith("https://"):
            raise FranceChimieMetadataRefusal("INVALID_REDIRECT", "Redirect source must use HTTPS.")
        if not isinstance(self.canonical_url, str) or not self.canonical_url.startswith("https://"):
            raise FranceChimieMetadataRefusal("INVALID_REDIRECT", "Redirect target must use HTTPS.")
        if self.previous_url == self.canonical_url:
            raise FranceChimieMetadataRefusal("INVALID_REDIRECT", "Redirect URLs must differ.")

    @classmethod
    def create(
        cls,
        previous_url: str,
        canonical_url: str,
        *,
        allowed_domains: frozenset[str],
    ) -> "FranceChimieRedirect":
        """Create a redirect only after applying the explicit local domain policy."""

        return cls(
            canonicalize_france_chimie_url(previous_url, allowed_domains=allowed_domains),
            canonicalize_france_chimie_url(canonical_url, allowed_domains=allowed_domains),
        )


class FranceChimieDocumentSync:
    """Compare injected metadata through public Document Registry operations only."""

    def __init__(self, registry: DocumentRegistry) -> None:
        if registry is None:
            raise FranceChimieMetadataRefusal(
                "REGISTRY_NOT_CONFIGURED",
                "Document Registry must be explicitly injected.",
            )
        self._registry = registry

    def compare_and_sync(
        self,
        metadata: tuple[FranceChimieMetadata, ...],
        *,
        detected_at: str,
        redirects: tuple[FranceChimieRedirect, ...] = (),
    ) -> tuple[FranceChimieSyncEvent, ...]:
        _validate_date(detected_at)
        if not isinstance(metadata, tuple) or any(not isinstance(item, FranceChimieMetadata) for item in metadata):
            raise FranceChimieMetadataRefusal(
                "INVALID_SYNC_BATCH",
                "France Chimie metadata must be an immutable tuple.",
            )
        if not isinstance(redirects, tuple) or any(not isinstance(item, FranceChimieRedirect) for item in redirects):
            raise FranceChimieMetadataRefusal(
                "INVALID_REDIRECT_BATCH",
                "Redirects must be an immutable tuple.",
            )

        incoming = _unique_by_url(metadata)
        known = self._registry.find_by_connector(FRANCE_CHIMIE_CONNECTOR_NAME)
        known_by_url = {item.canonical_url: item for item in known}
        redirect_by_new = _validate_redirects(redirects, known_by_url, incoming)
        processed: set[str] = set()
        events: list[FranceChimieSyncEvent] = []

        for canonical_url, item in sorted(incoming.items()):
            redirect = redirect_by_new.get(canonical_url)
            previous = known_by_url.get(redirect.previous_url) if redirect else known_by_url.get(canonical_url)
            if previous is None:
                document_id = stable_document_id(FRANCE_CHIMIE_CONNECTOR_NAME, canonical_url)
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


def _unique_by_url(metadata: tuple[FranceChimieMetadata, ...]) -> dict[str, FranceChimieMetadata]:
    result: dict[str, FranceChimieMetadata] = {}
    for item in metadata:
        if item.canonical_url in result:
            raise FranceChimieMetadataRefusal(
                "DUPLICATE_DOCUMENT",
                "Duplicate France Chimie metadata identity.",
            )
        result[item.canonical_url] = item
    return result


def _validate_redirects(
    redirects: tuple[FranceChimieRedirect, ...],
    known_by_url: dict[str, DocumentRecord],
    incoming: dict[str, FranceChimieMetadata],
) -> dict[str, FranceChimieRedirect]:
    result: dict[str, FranceChimieRedirect] = {}
    previous_urls: set[str] = set()
    for redirect in redirects:
        if redirect.previous_url in previous_urls or redirect.canonical_url in result:
            raise FranceChimieMetadataRefusal("DUPLICATE_REDIRECT", "Duplicate redirect declaration.")
        if redirect.previous_url not in known_by_url:
            raise FranceChimieMetadataRefusal(
                "UNKNOWN_REDIRECT_SOURCE",
                "Redirect source is absent from the registry.",
            )
        if redirect.canonical_url not in incoming:
            raise FranceChimieMetadataRefusal(
                "MISSING_REDIRECT_TARGET",
                "Redirect target metadata is required.",
            )
        previous_urls.add(redirect.previous_url)
        result[redirect.canonical_url] = redirect
    return result


def _to_record(
    item: FranceChimieMetadata,
    detected_at: str,
    *,
    document_id: str,
    first_seen: str | None = None,
    previous_status: DocumentStatus = DocumentStatus.ACTIVE,
    last_modified_metadata: str | None = None,
) -> DocumentRecord:
    return DocumentRecord(
        document_id=document_id,
        connector_name=FRANCE_CHIMIE_CONNECTOR_NAME,
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


def _event_from_change(change, detected_at: str) -> FranceChimieSyncEvent:
    event_type = {
        ChangeKind.NEW: FranceChimieSyncEventType.NEW,
        ChangeKind.UNCHANGED: FranceChimieSyncEventType.UNCHANGED,
        ChangeKind.REMOVED: FranceChimieSyncEventType.REMOVED,
        ChangeKind.REDIRECTED: FranceChimieSyncEventType.REDIRECTED,
    }.get(change.kind, FranceChimieSyncEventType.UPDATED)
    return FranceChimieSyncEvent(
        document_id=change.document_id,
        connector_name=FRANCE_CHIMIE_CONNECTOR_NAME,
        event_type=event_type,
        detected_at=detected_at,
        previous_snapshot=(
            FranceChimieDocumentSnapshot.from_record(change.previous) if change.previous else None
        ),
        new_snapshot=FranceChimieDocumentSnapshot.from_record(change.current) if change.current else None,
    )


def _validate_date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise FranceChimieMetadataRefusal(
            "INVALID_DETECTION_DATE",
            "Detection date must use ISO YYYY-MM-DD format.",
        ) from exc
