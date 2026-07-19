"""Behavior and persistence tests for the generic Document Registry."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from . import (
    ChangeKind, DocumentRecord, DocumentRegistry, DocumentStatus, DocumentValidator,
    DuplicateDocumentError, JsonDocumentStorage, stable_document_id,
)


CONNECTOR = "official_source"
URL = "https://official.example/public/item"


def record(**changes) -> DocumentRecord:
    values = {
        "document_id": stable_document_id(CONNECTOR, URL),
        "connector_name": CONNECTOR,
        "canonical_url": URL,
        "title": "Public metadata title",
        "category": "guidance",
        "family": "work",
        "document_type": "official_page",
        "publication_date": "2026-07-20",
        "first_seen": "2026-07-21",
        "last_checked": "2026-07-21",
        "last_modified_metadata": "2026-07-21",
        "language": "fr",
        "provenance": "official_source",
        "status": DocumentStatus.ACTIVE,
    }
    values.update(changes)
    return DocumentRecord(**values)


def registry(tmp_path) -> DocumentRegistry:
    storage = JsonDocumentStorage(tmp_path / "registry.json")
    validator = DocumentValidator({CONNECTOR: frozenset({"official.example"})})
    return DocumentRegistry(storage, validator)


def test_register_and_find_document(tmp_path):
    service = registry(tmp_path)
    change = service.register_document(record())
    assert change.kind is ChangeKind.NEW
    assert change.current.status is DocumentStatus.ACTIVE
    assert service.find_document(change.document_id) == change.current


def test_duplicate_registration_is_refused(tmp_path):
    service = registry(tmp_path)
    service.register_document(record())
    with pytest.raises(DuplicateDocumentError):
        service.register_document(record())


@pytest.mark.parametrize(("field", "value", "kind"), (
    ("title", "Changed title", ChangeKind.TITLE_CHANGED),
    ("publication_date", "2026-07-22", ChangeKind.DATE_CHANGED),
    ("category", "news", ChangeKind.CATEGORY_CHANGED),
    ("document_type", "press_release", ChangeKind.DOCUMENT_TYPE_CHANGED),
))
def test_specific_metadata_changes_are_detected(tmp_path, field, value, kind):
    service = registry(tmp_path)
    initial = service.register_document(record()).current
    candidate = replace(initial, **{field: value}, last_checked="2026-07-22")
    change = service.update_document(candidate)
    assert change.kind is kind
    assert change.current.status is DocumentStatus.UPDATED
    assert change.current.last_modified_metadata == "2026-07-22"


def test_unchanged_check_preserves_last_metadata_change(tmp_path):
    service = registry(tmp_path)
    initial = service.register_document(record()).current
    change = service.update_document(replace(initial, last_checked="2026-07-22"))
    assert change.kind is ChangeKind.UNCHANGED
    assert change.current.status is DocumentStatus.ACTIVE
    assert change.current.last_modified_metadata == "2026-07-21"


def test_logical_removal_and_removed_query(tmp_path):
    service = registry(tmp_path)
    initial = service.register_document(record()).current
    change = service.mark_removed(initial.document_id, checked_on="2026-07-22")
    assert change.kind is ChangeKind.REMOVED
    assert change.current.status is DocumentStatus.REMOVED
    assert service.find_removed_documents() == (change.current,)


def test_redirection_preserves_stable_document_identity(tmp_path):
    service = registry(tmp_path)
    initial = service.register_document(record()).current
    redirected = replace(initial, canonical_url="https://official.example/public/new-item", last_checked="2026-07-22")
    change = service.update_document(redirected)
    assert change.kind is ChangeKind.REDIRECTED
    assert change.current.status is DocumentStatus.REDIRECTED
    assert change.current.document_id == initial.document_id


def test_queries_by_connector_and_updated_status(tmp_path):
    service = registry(tmp_path)
    initial = service.register_document(record()).current
    updated = service.update_document(replace(initial, title="Updated", last_checked="2026-07-22")).current
    assert service.find_by_connector(CONNECTOR) == (updated,)
    assert service.find_by_connector("other_source") == ()
    assert service.find_updated_documents() == (updated,)


def test_json_storage_is_deterministic_and_metadata_only(tmp_path):
    path = tmp_path / "registry.json"
    service = DocumentRegistry(JsonDocumentStorage(path), DocumentValidator({CONNECTOR: frozenset({"official.example"})}))
    service.register_document(record())
    first = path.read_text(encoding="utf-8")
    reloaded = JsonDocumentStorage(path).load()
    JsonDocumentStorage(path).save(reloaded)
    assert path.read_text(encoding="utf-8") == first
    payload = json.loads(first)
    stored = payload["documents"][0]
    assert not set(stored) & {"text", "content", "html", "pdf", "excerpt", "embedding"}


def test_storage_boundary_is_replaceable_without_registry_cache():
    class CountingStorage:
        def __init__(self):
            self.documents = ()
            self.loads = 0

        def load(self):
            self.loads += 1
            return self.documents

        def save(self, documents):
            self.documents = documents

    storage = CountingStorage()
    service = DocumentRegistry(storage, DocumentValidator({CONNECTOR: frozenset({"official.example"})}))
    service.register_document(record())
    service.find_document(record().document_id)
    service.find_document(record().document_id)
    assert storage.loads == 3
