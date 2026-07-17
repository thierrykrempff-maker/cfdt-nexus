"""Deterministic in-memory ANACT metadata catalogue and version tracker."""
from dataclasses import replace

from automation.connector_platform.connector_fingerprint import fingerprint_metadata
from automation.connector_platform.connector_versioning import DocumentVersion, changed

from .anact_document_catalog_models import (
    CatalogChange,
    CatalogDocument,
    CatalogExport,
    CatalogLifecycle,
    CatalogQuery,
    CatalogVersionEvent,
)
from .anact_document_search import search_documents


class InMemoryAnactDocumentCatalog:
    schema_version = "anact-document-catalog-v1"

    def __init__(self) -> None:
        self._documents: dict[str, CatalogDocument] = {}
        self._aliases: dict[str, str] = {}
        self._versions: dict[str, list[DocumentVersion]] = {}

    def upsert(self, record: CatalogDocument) -> CatalogVersionEvent:
        matching_ids = {self._aliases[alias] for alias in record.aliases if alias in self._aliases}
        if matching_ids:
            document_id = min(matching_ids)
            aliases = set(record.aliases)
            for matched_id in sorted(matching_ids):
                previous_record = self._documents.get(matched_id)
                if previous_record:
                    aliases.update(previous_record.aliases)
                if matched_id != document_id:
                    self._remove_duplicate(matched_id, document_id)
            record = record.with_identity(document_id, tuple(sorted(aliases)))
            previous = self._documents[document_id]
            same = previous.metadata_fingerprint == record.metadata_fingerprint
            same = same and previous.lifecycle is CatalogLifecycle.ACTIVE
            change = CatalogChange.UNCHANGED if same else CatalogChange.MODIFIED
        else:
            change = CatalogChange.NEW

        self._documents[record.document_id] = record
        self._register_aliases(record)
        version = None if change is CatalogChange.UNCHANGED else self._append_version(record, change)
        return CatalogVersionEvent(change, record, version)

    def reconcile(self, records: tuple[CatalogDocument, ...]) -> tuple[CatalogVersionEvent, ...]:
        events: dict[str, CatalogVersionEvent] = {}
        rank = {CatalogChange.UNCHANGED: 0, CatalogChange.MODIFIED: 1, CatalogChange.NEW: 2}
        observed: set[str] = set()
        for record in sorted(records, key=lambda item: (item.canonical_url, item.metadata_fingerprint)):
            event = self.upsert(record)
            observed.add(event.document.document_id)
            existing = events.get(event.document.document_id)
            if existing is None or rank[event.change] > rank[existing.change]:
                events[event.document.document_id] = event
        for document_id, record in sorted(tuple(self._documents.items())):
            if record.lifecycle is CatalogLifecycle.ACTIVE and document_id not in observed:
                disappeared = record.with_lifecycle(CatalogLifecycle.DISAPPEARED)
                self._documents[document_id] = disappeared
                event = CatalogVersionEvent(CatalogChange.DISAPPEARED, disappeared, self._append_version(disappeared, CatalogChange.DISAPPEARED))
                events[document_id] = event
        return tuple(events[key] for key in sorted(events))

    def records(self) -> tuple[CatalogDocument, ...]:
        return tuple(self._documents[key] for key in sorted(self._documents))

    def get(self, document_id: str) -> CatalogDocument:
        try:
            return self._documents[document_id]
        except KeyError as error:
            raise KeyError("unknown catalogue document") from error

    def versions(self, document_id: str | None = None) -> tuple[DocumentVersion, ...]:
        if document_id is not None:
            return tuple(self._versions.get(document_id, ()))
        return tuple(version for key in sorted(self._versions) for version in self._versions[key])

    def search(self, query: CatalogQuery = CatalogQuery()) -> tuple[CatalogDocument, ...]:
        return search_documents(self.records(), query)

    def export(self) -> CatalogExport:
        return CatalogExport(self.schema_version, self.records(), self.versions())

    def _append_version(self, record: CatalogDocument, change: CatalogChange) -> DocumentVersion:
        history = self._versions.setdefault(record.document_id, [])
        previous = history[-1] if history else None
        fingerprint = record.version_fingerprint()
        version_id = fingerprint_metadata((record.document_id, fingerprint, str(len(history) + 1), change.value))
        version = DocumentVersion(record.document_id, version_id, fingerprint, previous.version_id if previous else None)
        if previous is not None and change is CatalogChange.MODIFIED and not changed(previous, version):
            raise ValueError("modified version requires a changed fingerprint")
        history.append(version)
        return version

    def _register_aliases(self, record: CatalogDocument) -> None:
        for alias in record.aliases:
            self._aliases[alias] = record.document_id

    def _remove_duplicate(self, duplicate_id: str, retained_id: str) -> None:
        self._documents.pop(duplicate_id, None)
        self._versions.pop(duplicate_id, None)
        for alias, document_id in tuple(self._aliases.items()):
            if document_id == duplicate_id:
                self._aliases[alias] = retained_id
