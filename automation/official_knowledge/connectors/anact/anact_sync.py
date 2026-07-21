"""Pure offline synchronization of ANACT metadata inventories."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from automation.official_knowledge.document_registry import (
    DocumentRecord,
    DocumentStatus,
    stable_document_id,
)

from .anact_models import ANACT_CONNECTOR_NAME, AnactResource


class AnactSyncError(ValueError):
    """Fail-closed synchronization error with a stable non-sensitive code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class AnactSyncEventType(str, Enum):
    NEW = "NEW"
    UPDATED = "UPDATED"
    REMOVED = "REMOVED"
    REDIRECTED = "REDIRECTED"
    UNCHANGED = "UNCHANGED"


@dataclass(frozen=True)
class AnactDocumentSnapshot:
    """Immutable, content-free ANACT metadata carried by an event."""

    document_id: str
    reference: str
    canonical_url: str
    title: str
    publication_date: str | None
    category: str
    family: str
    document_type: str
    provenance: str
    language: str
    metadata_hash: str
    status: DocumentStatus

    @classmethod
    def from_resource(
        cls,
        resource: AnactResource,
        *,
        document_id: str | None = None,
        status: DocumentStatus = DocumentStatus.ACTIVE,
    ) -> "AnactDocumentSnapshot":
        expected = stable_document_id(ANACT_CONNECTOR_NAME, resource.canonical_url)
        return cls(
            document_id=document_id or expected,
            reference=resource.resource_id,
            canonical_url=resource.canonical_url,
            title=resource.title,
            publication_date=resource.published_at,
            category=resource.theme.value,
            family=resource.scope.value,
            document_type=resource.resource_type.value,
            provenance=ANACT_CONNECTOR_NAME,
            language=resource.language,
            metadata_hash=resource.fingerprint(),
            status=status,
        )

    def to_document_record(
        self,
        *,
        checked_on: str,
        first_seen: str | None = None,
        last_modified_metadata: str | None = None,
    ) -> DocumentRecord:
        """Convert through the public, metadata-only Document Registry model."""

        _validate_date(checked_on)
        if first_seen is not None:
            _validate_date(first_seen)
        if last_modified_metadata is not None:
            _validate_date(last_modified_metadata)
        return DocumentRecord(
            document_id=self.document_id,
            connector_name=ANACT_CONNECTOR_NAME,
            canonical_url=self.canonical_url,
            title=self.title,
            category=self.category,
            family=self.family,
            document_type=self.document_type,
            publication_date=self.publication_date,
            first_seen=first_seen or checked_on,
            last_checked=checked_on,
            last_modified_metadata=last_modified_metadata or checked_on,
            language=self.language,
            provenance=self.provenance,
            status=self.status,
        )


@dataclass(frozen=True)
class AnactSyncEvent:
    document_id: str
    connector_name: str
    event_type: AnactSyncEventType
    detected_at: str
    previous_snapshot: AnactDocumentSnapshot | None
    new_snapshot: AnactDocumentSnapshot | None
    changed_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.connector_name != ANACT_CONNECTOR_NAME:
            raise ValueError("invalid ANACT synchronization event connector")
        if not isinstance(self.event_type, AnactSyncEventType):
            raise TypeError("event_type must be an AnactSyncEventType")
        _validate_date(self.detected_at)


@dataclass(frozen=True)
class AnactRedirect:
    previous_url: str
    canonical_url: str

    def __post_init__(self) -> None:
        if not _is_https_url(self.previous_url) or not _is_https_url(self.canonical_url):
            raise AnactSyncError("INVALID_REDIRECT", "Redirect URLs must use HTTPS.")
        if self.previous_url == self.canonical_url:
            raise AnactSyncError("INVALID_REDIRECT", "Redirect URLs must differ.")


class AnactDocumentSync:
    """Compare two injected ANACT inventories without transport or persistence."""

    def compare_inventories(
        self,
        previous_inventory: tuple[AnactResource, ...],
        new_inventory: tuple[AnactResource, ...],
        *,
        detected_at: str,
        redirects: tuple[AnactRedirect, ...] = (),
    ) -> tuple[AnactSyncEvent, ...]:
        _validate_date(detected_at)
        previous = _unique_by_url(previous_inventory, "previous")
        current = _unique_by_url(new_inventory, "new")
        redirect_by_target = _validate_redirects(redirects, previous, current)
        processed_previous: set[str] = set()
        events: list[AnactSyncEvent] = []

        for canonical_url, resource in sorted(current.items()):
            redirect = redirect_by_target.get(canonical_url)
            if redirect is not None:
                old_resource = previous[redirect.previous_url]
                previous_snapshot = AnactDocumentSnapshot.from_resource(old_resource)
                current_snapshot = AnactDocumentSnapshot.from_resource(
                    resource,
                    document_id=previous_snapshot.document_id,
                    status=DocumentStatus.REDIRECTED,
                )
                processed_previous.add(redirect.previous_url)
                events.append(
                    AnactSyncEvent(
                        document_id=previous_snapshot.document_id,
                        connector_name=ANACT_CONNECTOR_NAME,
                        event_type=AnactSyncEventType.REDIRECTED,
                        detected_at=detected_at,
                        previous_snapshot=previous_snapshot,
                        new_snapshot=current_snapshot,
                        changed_fields=_changed_fields(previous_snapshot, current_snapshot),
                    )
                )
                continue

            old_resource = previous.get(canonical_url)
            current_snapshot = AnactDocumentSnapshot.from_resource(resource)
            if old_resource is None:
                events.append(
                    AnactSyncEvent(
                        document_id=current_snapshot.document_id,
                        connector_name=ANACT_CONNECTOR_NAME,
                        event_type=AnactSyncEventType.NEW,
                        detected_at=detected_at,
                        previous_snapshot=None,
                        new_snapshot=current_snapshot,
                    )
                )
                continue

            processed_previous.add(canonical_url)
            previous_snapshot = AnactDocumentSnapshot.from_resource(old_resource)
            changed_fields = _changed_fields(previous_snapshot, current_snapshot)
            event_type = AnactSyncEventType.UPDATED if changed_fields else AnactSyncEventType.UNCHANGED
            if event_type is AnactSyncEventType.UPDATED:
                current_snapshot = AnactDocumentSnapshot.from_resource(
                    resource,
                    status=DocumentStatus.UPDATED,
                )
            events.append(
                AnactSyncEvent(
                    document_id=current_snapshot.document_id,
                    connector_name=ANACT_CONNECTOR_NAME,
                    event_type=event_type,
                    detected_at=detected_at,
                    previous_snapshot=previous_snapshot,
                    new_snapshot=current_snapshot,
                    changed_fields=changed_fields,
                )
            )

        for canonical_url, resource in sorted(previous.items()):
            if canonical_url in processed_previous:
                continue
            previous_snapshot = AnactDocumentSnapshot.from_resource(resource)
            removed_snapshot = AnactDocumentSnapshot.from_resource(
                resource,
                status=DocumentStatus.REMOVED,
            )
            events.append(
                AnactSyncEvent(
                    document_id=previous_snapshot.document_id,
                    connector_name=ANACT_CONNECTOR_NAME,
                    event_type=AnactSyncEventType.REMOVED,
                    detected_at=detected_at,
                    previous_snapshot=previous_snapshot,
                    new_snapshot=removed_snapshot,
                    changed_fields=("status",),
                )
            )

        return tuple(sorted(events, key=lambda event: (event.document_id, event.event_type.value)))


def _unique_by_url(
    inventory: tuple[AnactResource, ...],
    label: str,
) -> dict[str, AnactResource]:
    if not isinstance(inventory, tuple) or any(not isinstance(item, AnactResource) for item in inventory):
        raise AnactSyncError("INVALID_INVENTORY", f"The {label} inventory must be an immutable ANACT tuple.")
    result: dict[str, AnactResource] = {}
    for resource in inventory:
        if resource.canonical_url in result:
            raise AnactSyncError("DUPLICATE_DOCUMENT", "Duplicate ANACT canonical URL.")
        expected = stable_document_id(ANACT_CONNECTOR_NAME, resource.canonical_url)
        if resource.document_id != expected:
            raise AnactSyncError("UNSTABLE_DOCUMENT_ID", "ANACT identity must use the common stable identifier.")
        result[resource.canonical_url] = resource
    return result


def _validate_redirects(
    redirects: tuple[AnactRedirect, ...],
    previous: dict[str, AnactResource],
    current: dict[str, AnactResource],
) -> dict[str, AnactRedirect]:
    if not isinstance(redirects, tuple) or any(not isinstance(item, AnactRedirect) for item in redirects):
        raise AnactSyncError("INVALID_REDIRECT_BATCH", "Redirects must be an immutable ANACT tuple.")
    result: dict[str, AnactRedirect] = {}
    sources: set[str] = set()
    for redirect in redirects:
        if redirect.previous_url in sources or redirect.canonical_url in result:
            raise AnactSyncError("DUPLICATE_REDIRECT", "Duplicate ANACT redirect declaration.")
        if redirect.previous_url not in previous:
            raise AnactSyncError("UNKNOWN_REDIRECT_SOURCE", "Redirect source is absent from the old inventory.")
        if redirect.canonical_url not in current:
            raise AnactSyncError("MISSING_REDIRECT_TARGET", "Redirect target is absent from the new inventory.")
        sources.add(redirect.previous_url)
        result[redirect.canonical_url] = redirect
    return result


def _changed_fields(
    previous: AnactDocumentSnapshot,
    current: AnactDocumentSnapshot,
) -> tuple[str, ...]:
    comparable = (
        "canonical_url",
        "reference",
        "title",
        "publication_date",
        "category",
        "family",
        "document_type",
        "provenance",
        "language",
        "metadata_hash",
    )
    return tuple(name for name in comparable if getattr(previous, name) != getattr(current, name))


def _validate_date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise AnactSyncError("INVALID_DETECTION_DATE", "Date must use ISO YYYY-MM-DD format.") from exc


def _is_https_url(value: object) -> bool:
    return isinstance(value, str) and value.startswith("https://") and len(value) > len("https://")
