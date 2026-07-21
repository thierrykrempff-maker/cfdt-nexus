"""CARSAT metadata-only synchronization tests."""

import ast
import unittest
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

from automation.official_knowledge.document_registry import DocumentRecord, DocumentRegistry, DocumentStatus, DocumentValidator

from .carsat_metadata import CarsatMetadata, CarsatMetadataRefusal
from .carsat_sync import CarsatDocumentSync, CarsatRedirect, CarsatSyncEventType


SYNTHETIC_DOMAIN = "carsat.example.invalid"


class MemoryStorage:
    def __init__(self) -> None:
        self.documents: tuple[DocumentRecord, ...] = ()

    def load(self) -> tuple[DocumentRecord, ...]:
        return self.documents

    def save(self, documents: tuple[DocumentRecord, ...]) -> None:
        self.documents = documents


def metadata(url: str = f"https://{SYNTHETIC_DOMAIN}/publication-a", **changes) -> CarsatMetadata:
    values = {
        "canonical_url": url,
        "title": "Publication synthétique",
        "publication_date": "2026-07-01",
        "category": "prevention",
        "family": "prevention_guide",
        "document_type": "guide",
        "discovered_at": "2026-07-19",
        "reference": "SYNTHETIC-001",
    }
    values.update(changes)
    return CarsatMetadata.create(**values)


class CarsatDocumentSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.storage = MemoryStorage()
        validator = DocumentValidator({"carsat": frozenset({SYNTHETIC_DOMAIN})})
        self.registry = DocumentRegistry(self.storage, validator)
        self.sync = CarsatDocumentSync(self.registry)

    def first_sync(self):
        return self.sync.compare_and_sync((metadata(),), detected_at="2026-07-19")[0]

    def test_registry_injection_required(self):
        with self.assertRaises(CarsatMetadataRefusal):
            CarsatDocumentSync(None)  # type: ignore[arg-type]

    def test_new(self):
        item = metadata()
        event = self.sync.compare_and_sync((item,), detected_at="2026-07-19")[0]
        self.assertIs(CarsatSyncEventType.NEW, event.event_type)
        self.assertEqual(item.document_id, event.document_id)
        self.assertIsNone(event.previous_snapshot)

    def test_unchanged_and_idempotent(self):
        self.first_sync()
        first = self.sync.compare_and_sync((metadata(),), detected_at="2026-07-20")[0]
        second = self.sync.compare_and_sync((metadata(),), detected_at="2026-07-20")[0]
        self.assertIs(CarsatSyncEventType.UNCHANGED, first.event_type)
        self.assertEqual(first, second)

    def test_updated_metadata(self):
        for field, value in (("title", "Titre modifié"), ("publication_date", "2026-07-02"), ("category", "at_mp"), ("family", "practical_sheet"), ("document_type", "fiche")):
            with self.subTest(field=field):
                storage = MemoryStorage()
                engine = CarsatDocumentSync(DocumentRegistry(storage, DocumentValidator({"carsat": frozenset({SYNTHETIC_DOMAIN})})))
                engine.compare_and_sync((metadata(),), detected_at="2026-07-19")
                event = engine.compare_and_sync((metadata(**{field: value}),), detected_at="2026-07-20")[0]
                self.assertIs(CarsatSyncEventType.UPDATED, event.event_type)

    def test_removed_once(self):
        original = self.first_sync()
        event = self.sync.compare_and_sync((), detected_at="2026-07-20")[0]
        self.assertIs(CarsatSyncEventType.REMOVED, event.event_type)
        self.assertEqual(original.document_id, event.document_id)
        self.assertEqual(DocumentStatus.REMOVED.value, event.new_snapshot.status)
        self.assertEqual((), self.sync.compare_and_sync((), detected_at="2026-07-21"))

    def test_redirect_preserves_identity(self):
        original = self.first_sync()
        target = metadata(f"https://{SYNTHETIC_DOMAIN}/publication-b")
        event = self.sync.compare_and_sync(
            (target,), detected_at="2026-07-20",
            redirects=(CarsatRedirect(f"https://{SYNTHETIC_DOMAIN}/publication-a", target.canonical_url),),
        )[0]
        self.assertIs(CarsatSyncEventType.REDIRECTED, event.event_type)
        self.assertEqual(original.document_id, event.document_id)

    def test_invalid_redirects_fail_closed(self):
        self.first_sync()
        target = metadata(f"https://{SYNTHETIC_DOMAIN}/publication-b")
        with self.assertRaises(CarsatMetadataRefusal):
            self.sync.compare_and_sync((target,), detected_at="2026-07-20", redirects=(CarsatRedirect(f"https://{SYNTHETIC_DOMAIN}/unknown", target.canonical_url),))
        with self.assertRaises(CarsatMetadataRefusal):
            self.sync.compare_and_sync((), detected_at="2026-07-20", redirects=(CarsatRedirect(f"https://{SYNTHETIC_DOMAIN}/publication-a", target.canonical_url),))

    def test_events_are_immutable_and_ordered(self):
        events = self.sync.compare_and_sync(
            (metadata(f"https://{SYNTHETIC_DOMAIN}/z"), metadata(f"https://{SYNTHETIC_DOMAIN}/a")),
            detected_at="2026-07-19",
        )
        self.assertEqual(sorted(item.document_id for item in events), [item.document_id for item in events])
        with self.assertRaises(FrozenInstanceError):
            events[0].detected_at = "2026-07-20"  # type: ignore[misc]

    def test_duplicate_refused(self):
        item = metadata()
        with self.assertRaises(CarsatMetadataRefusal):
            self.sync.compare_and_sync((item, item), detected_at="2026-07-19")

    def test_registry_compatibility(self):
        self.first_sync()
        record = self.registry.find_by_connector("carsat")[0]
        self.assertEqual("carsat", record.connector_name)
        self.assertEqual(1, len(self.storage.documents))

    def test_metadata_only_models(self):
        forbidden = {"body", "content", "text", "excerpt", "summary", "html", "pdf", "binary", "attachment"}
        self.assertTrue(forbidden.isdisjoint(field.name for field in fields(CarsatMetadata)))
        self.assertTrue(forbidden.isdisjoint(field.name for field in fields(type(self.first_sync().new_snapshot))))

    def test_https_and_pdf_guards(self):
        with self.assertRaises(CarsatMetadataRefusal):
            metadata("http://carsat.example.invalid/item")
        with self.assertRaises(CarsatMetadataRefusal):
            metadata("https://carsat.example.invalid/item.pdf")

    def test_no_network_import(self):
        forbidden = {"requests", "httpx", "aiohttp", "urllib", "urllib.request", "http.client", "socket"}
        for name in ("carsat_metadata.py", "carsat_sync.py"):
            path = Path(__file__).with_name(name)
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module)
            self.assertTrue(forbidden.isdisjoint(imports))


if __name__ == "__main__":
    unittest.main()
