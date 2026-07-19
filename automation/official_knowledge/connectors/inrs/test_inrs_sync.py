"""Metadata-only synchronization tests for INRS LOT 2."""

import ast
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from automation.official_knowledge.document_registry import (
    DocumentRecord,
    DocumentRegistry,
    DocumentStatus,
    DocumentValidator,
)

from .inrs_metadata import INRS_SOURCE_DOMAIN, InrsMetadata, InrsMetadataRefusal, metadata_from_mapping
from .inrs_sync import InrsDocumentSync, InrsRedirect, InrsSyncEvent, InrsSyncEventType


class MemoryStorage:
    def __init__(self) -> None:
        self.documents: tuple[DocumentRecord, ...] = ()
        self.operations: list[str] = []

    def load(self) -> tuple[DocumentRecord, ...]:
        self.operations.append("load")
        return self.documents

    def save(self, documents: tuple[DocumentRecord, ...]) -> None:
        self.operations.append("save")
        self.documents = documents


def metadata(url: str = "https://www.inrs.fr/publications/ed-0000", **changes) -> InrsMetadata:
    values = {
        "url": url,
        "title": "Publication synthétique",
        "document_type": "brochure",
        "category": "prévention",
        "family": "risques_chimiques",
        "publication_date": "2026-07-01",
        "last_modified_date": "2026-07-02",
        "language": "fr",
        "discovered_at": "2026-07-19",
        "reference": None,
    }
    values.update(changes)
    return metadata_from_mapping(values)


class InrsDocumentSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.storage = MemoryStorage()
        validator = DocumentValidator({"inrs": frozenset({INRS_SOURCE_DOMAIN})})
        self.registry = DocumentRegistry(self.storage, validator)
        self.sync = InrsDocumentSync(self.registry)

    def first_sync(self) -> InrsSyncEvent:
        return self.sync.compare_and_sync((metadata(),), detected_at="2026-07-19")[0]

    def test_registry_injection_is_mandatory(self) -> None:
        with self.assertRaisesRegex(InrsMetadataRefusal, "explicitly"):
            InrsDocumentSync(None)  # type: ignore[arg-type]

    def test_new_document(self) -> None:
        event = self.first_sync()
        self.assertIs(InrsSyncEventType.NEW, event.event_type)
        self.assertEqual("inrs", event.connector_name)
        self.assertIsNone(event.previous_snapshot)
        self.assertIsNotNone(event.new_snapshot)

    def test_unchanged_document(self) -> None:
        self.first_sync()
        event = self.sync.compare_and_sync((metadata(),), detected_at="2026-07-20")[0]
        self.assertIs(InrsSyncEventType.UNCHANGED, event.event_type)
        self.assertEqual(event.previous_snapshot.title, event.new_snapshot.title)

    def test_metadata_updates(self) -> None:
        changes = (
            ("title", "Titre modifié"),
            ("publication_date", "2026-07-03"),
            ("category", "sécurité"),
            ("family", "RPS"),
            ("document_type", "guide"),
        )
        for field, value in changes:
            with self.subTest(field=field):
                storage = MemoryStorage()
                registry = DocumentRegistry(storage, DocumentValidator({"inrs": frozenset({INRS_SOURCE_DOMAIN})}))
                engine = InrsDocumentSync(registry)
                engine.compare_and_sync((metadata(),), detected_at="2026-07-19")
                event = engine.compare_and_sync((metadata(**{field: value}),), detected_at="2026-07-20")[0]
                self.assertIs(InrsSyncEventType.UPDATED, event.event_type)

    def test_logical_removal(self) -> None:
        first = self.first_sync()
        event = self.sync.compare_and_sync((), detected_at="2026-07-20")[0]
        self.assertIs(InrsSyncEventType.REMOVED, event.event_type)
        self.assertEqual(first.document_id, event.document_id)
        self.assertEqual(DocumentStatus.REMOVED.value, event.new_snapshot.status)
        self.assertEqual(1, len(self.registry.find_removed_documents()))

    def test_removal_is_idempotent(self) -> None:
        self.first_sync()
        self.sync.compare_and_sync((), detected_at="2026-07-20")
        self.assertEqual((), self.sync.compare_and_sync((), detected_at="2026-07-21"))

    def test_redirect_preserves_document_id(self) -> None:
        first = self.first_sync()
        target = metadata("https://www.inrs.fr/publications/ed-0000-new")
        event = self.sync.compare_and_sync(
            (target,),
            detected_at="2026-07-20",
            redirects=(InrsRedirect("https://www.inrs.fr/publications/ed-0000", target.canonical_url),),
        )[0]
        self.assertIs(InrsSyncEventType.REDIRECTED, event.event_type)
        self.assertEqual(first.document_id, event.document_id)
        self.assertEqual("https://www.inrs.fr/publications/ed-0000", event.previous_snapshot.canonical_url)
        self.assertEqual(target.canonical_url, event.new_snapshot.canonical_url)

    def test_invalid_redirects_fail_closed(self) -> None:
        self.first_sync()
        target = metadata("https://www.inrs.fr/publications/new")
        with self.assertRaisesRegex(InrsMetadataRefusal, "absent"):
            self.sync.compare_and_sync(
                (target,), detected_at="2026-07-20",
                redirects=(InrsRedirect("https://www.inrs.fr/publications/unknown", target.canonical_url),),
            )
        with self.assertRaisesRegex(InrsMetadataRefusal, "target"):
            self.sync.compare_and_sync(
                (), detected_at="2026-07-20",
                redirects=(InrsRedirect("https://www.inrs.fr/publications/ed-0000", target.canonical_url),),
            )

    def test_events_are_immutable_and_structured(self) -> None:
        event = self.first_sync()
        self.assertIsInstance(event, InrsSyncEvent)
        with self.assertRaises(FrozenInstanceError):
            event.detected_at = "2026-07-20"  # type: ignore[misc]
        self.assertEqual(
            {"document_id", "connector_name", "event_type", "detected_at", "previous_snapshot", "new_snapshot"},
            set(event.__dataclass_fields__),
        )

    def test_order_is_stable_and_reproducible(self) -> None:
        items = (
            metadata("https://www.inrs.fr/publications/z"),
            metadata("https://www.inrs.fr/publications/a"),
        )
        first = self.sync.compare_and_sync(items, detected_at="2026-07-19")
        self.assertEqual(sorted(event.document_id for event in first), [event.document_id for event in first])
        second_storage = MemoryStorage()
        second_sync = InrsDocumentSync(DocumentRegistry(second_storage, DocumentValidator({"inrs": frozenset({INRS_SOURCE_DOMAIN})})))
        second = second_sync.compare_and_sync(tuple(reversed(items)), detected_at="2026-07-19")
        self.assertEqual(first, second)

    def test_duplicate_url_and_identity_are_rejected(self) -> None:
        item = metadata()
        with self.assertRaisesRegex(InrsMetadataRefusal, "Duplicate"):
            self.sync.compare_and_sync((item, item), detected_at="2026-07-19")
        same_reference = metadata("https://www.inrs.fr/publications/other", reference="ED 1")
        other_url_same_reference = metadata("https://www.inrs.fr/publications/another", reference="ED-1")
        with self.assertRaisesRegex(InrsMetadataRefusal, "Duplicate"):
            self.sync.compare_and_sync((same_reference, other_url_same_reference), detected_at="2026-07-19")

    def test_invalid_detection_date_is_rejected(self) -> None:
        with self.assertRaisesRegex(InrsMetadataRefusal, "ISO"):
            self.sync.compare_and_sync((metadata(),), detected_at="19/07/2026")

    def test_registry_uses_only_public_interface_effects(self) -> None:
        self.first_sync()
        self.assertTrue(self.storage.operations)
        self.assertTrue(set(self.storage.operations) <= {"load", "save"})
        self.assertEqual(1, len(self.registry.find_by_connector("inrs")))

    def test_snapshots_and_records_have_no_content_fields(self) -> None:
        event = self.first_sync()
        forbidden = {"body", "content", "text", "excerpt", "summary", "html", "pdf", "binary", "attachment"}
        self.assertTrue(forbidden.isdisjoint(event.new_snapshot.__dataclass_fields__))
        self.assertTrue(forbidden.isdisjoint(self.registry.find_by_connector("inrs")[0].to_dict()))

    def test_sync_module_has_no_network_client(self) -> None:
        path = Path(__file__).with_name("inrs_sync.py")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        forbidden = {"requests", "httpx", "aiohttp", "urllib", "urllib.request", "http.client", "socket"}
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        self.assertTrue(forbidden.isdisjoint(imports))


if __name__ == "__main__":
    unittest.main()
