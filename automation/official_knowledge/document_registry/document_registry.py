"""Generic metadata-only registry and deterministic change detection."""

from __future__ import annotations

from dataclasses import replace

from .document_models import ChangeKind, DocumentChange, DocumentRecord, DocumentStatus
from .document_validation import DocumentValidator
from .registry_storage import DocumentStorage


class DocumentNotFoundError(LookupError):
    pass


class DuplicateDocumentError(ValueError):
    pass


class DocumentRegistry:
    """Stateless service: storage is loaded for every public operation."""

    _TRACKED_FIELDS = ("title", "publication_date", "category", "family", "document_type", "language", "provenance")

    def __init__(self, storage: DocumentStorage, validator: DocumentValidator) -> None:
        self._storage = storage
        self._validator = validator

    def register_document(self, document: DocumentRecord) -> DocumentChange:
        self._validator.validate_new(document)
        documents = self._by_id()
        if document.document_id in documents:
            raise DuplicateDocumentError(f"document already registered: {document.document_id}")
        current = replace(document, status=DocumentStatus.ACTIVE)
        documents[current.document_id] = current
        self._save(documents)
        return DocumentChange(current.document_id, ChangeKind.NEW, None, current)

    def update_document(self, document: DocumentRecord) -> DocumentChange:
        self._validator.validate(document)
        documents = self._by_id()
        previous = documents.get(document.document_id)
        if previous is None:
            raise DocumentNotFoundError(document.document_id)
        if document.connector_name != previous.connector_name or document.first_seen != previous.first_seen:
            raise ValueError("connector_name and first_seen are immutable")
        if document.last_checked < previous.last_checked:
            raise ValueError("last_checked cannot move backwards")
        changed = tuple(name for name in self._TRACKED_FIELDS if getattr(previous, name) != getattr(document, name))
        redirected = previous.canonical_url != document.canonical_url
        if redirected:
            kind = ChangeKind.REDIRECTED
            status = DocumentStatus.REDIRECTED
            changed = ("canonical_url",) + changed
        elif changed:
            kind = _specific_change(changed)
            status = DocumentStatus.UPDATED
        else:
            kind = ChangeKind.UNCHANGED
            status = DocumentStatus.ACTIVE
        modified_on = document.last_checked if redirected or changed else previous.last_modified_metadata
        current = replace(document, status=status, last_modified_metadata=modified_on)
        self._validator.validate(current)
        documents[current.document_id] = current
        self._save(documents)
        return DocumentChange(current.document_id, kind, previous, current, changed)

    def mark_removed(self, document_id: str, *, checked_on: str) -> DocumentChange:
        documents = self._by_id()
        previous = documents.get(document_id)
        if previous is None:
            raise DocumentNotFoundError(document_id)
        current = replace(previous, status=DocumentStatus.REMOVED, last_checked=checked_on, last_modified_metadata=checked_on)
        self._validator.validate(current)
        documents[document_id] = current
        self._save(documents)
        return DocumentChange(document_id, ChangeKind.REMOVED, previous, current, ("status",))

    def find_document(self, document_id: str) -> DocumentRecord | None:
        return self._by_id().get(document_id)

    def find_by_connector(self, connector_name: str) -> tuple[DocumentRecord, ...]:
        return tuple(item for item in self._load() if item.connector_name == connector_name)

    def find_updated_documents(self) -> tuple[DocumentRecord, ...]:
        return tuple(item for item in self._load() if item.status is DocumentStatus.UPDATED)

    def find_removed_documents(self) -> tuple[DocumentRecord, ...]:
        return tuple(item for item in self._load() if item.status is DocumentStatus.REMOVED)

    def _load(self) -> tuple[DocumentRecord, ...]:
        documents = self._storage.load()
        for item in documents:
            self._validator.validate(item)
        return tuple(sorted(documents, key=lambda item: item.document_id))

    def _by_id(self) -> dict[str, DocumentRecord]:
        return {item.document_id: item for item in self._load()}

    def _save(self, documents: dict[str, DocumentRecord]) -> None:
        self._storage.save(tuple(sorted(documents.values(), key=lambda item: item.document_id)))


def _specific_change(changed: tuple[str, ...]) -> ChangeKind:
    if len(changed) != 1:
        return ChangeKind.METADATA_CHANGED
    return {
        "title": ChangeKind.TITLE_CHANGED,
        "publication_date": ChangeKind.DATE_CHANGED,
        "category": ChangeKind.CATEGORY_CHANGED,
        "family": ChangeKind.FAMILY_CHANGED,
        "document_type": ChangeKind.DOCUMENT_TYPE_CHANGED,
    }.get(changed[0], ChangeKind.METADATA_CHANGED)
