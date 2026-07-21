"""Offline France Chimie document synchronization tests."""

import ast
import unittest
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

from automation.official_knowledge.document_registry import (
    DocumentRecord,
    DocumentRegistry,
    DocumentStatus,
    DocumentValidator,
    stable_document_id,
)

from .france_chimie_metadata import FranceChimieMetadata, FranceChimieMetadataRefusal, metadata_from_mapping
from .france_chimie_sync import (
    FranceChimieDocumentSync,
    FranceChimieRedirect,
    FranceChimieSyncEventType,
)


SYNTHETIC_DOMAIN = "france-chimie.example.invalid"
SYNTHETIC_DOMAINS = frozenset({SYNTHETIC_DOMAIN})


class MemoryStorage:
    def __init__(self) -> None:
        self.documents: tuple[DocumentRecord, ...] = ()

    def load(self) -> tuple[DocumentRecord, ...]:
        return self.documents

    def save(self, documents: tuple[DocumentRecord, ...]) -> None:
        self.documents = documents


def metadata(url: str = f"https://{SYNTHETIC_DOMAIN}/publication-a", **changes) -> FranceChimieMetadata:
    value = {
        "url": url,
        "title": "Publication France Chimie synthétique",
        "publication_date": "2026-07-01",
        "category": "prevention",
        "family": "chemical_risk",
        "document_type": "practical_sheet",
        "language": "fr",
        "discovered_at": "2026-07-21",
        "reference": "SYNTHETIC-001",
    }
    value.update(changes)
    return metadata_from_mapping(value, allowed_domains=SYNTHETIC_DOMAINS)


class FranceChimieDocumentSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.storage = MemoryStorage()
        validator = DocumentValidator({"france_chimie": SYNTHETIC_DOMAINS})
        self.registry = DocumentRegistry(self.storage, validator)
        self.sync = FranceChimieDocumentSync(self.registry)

    def first_sync(self):
        return self.sync.compare_and_sync((metadata(),), detected_at="2026-07-21")[0]

    def test_registry_injection_is_required(self) -> None:
        with self.assertRaises(FranceChimieMetadataRefusal):
            FranceChimieDocumentSync(None)  # type: ignore[arg-type]

    def test_new_document_uses_common_stable_identity(self) -> None:
        item = metadata()
        event = self.sync.compare_and_sync((item,), detected_at="2026-07-21")[0]
        self.assertIs(FranceChimieSyncEventType.NEW, event.event_type)
        self.assertEqual(stable_document_id("france_chimie", item.canonical_url), event.document_id)
        self.assertEqual(item.document_id, event.document_id)
        self.assertIsNone(event.previous_snapshot)

    def test_unchanged_document_is_idempotent(self) -> None:
        self.first_sync()
        first = self.sync.compare_and_sync((metadata(),), detected_at="2026-07-22")[0]
        second = self.sync.compare_and_sync((metadata(),), detected_at="2026-07-22")[0]
        self.assertIs(FranceChimieSyncEventType.UNCHANGED, first.event_type)
        self.assertEqual(first, second)

    def test_metadata_updates(self) -> None:
        changes = (
            ("title", "Titre synthétique modifié"),
            ("publication_date", "2026-07-02"),
            ("category", "social_dialogue"),
            ("family", "social_dialogue"),
            ("document_type", "guide"),
            ("language", "en"),
        )
        for field_name, value in changes:
            with self.subTest(field=field_name):
                storage = MemoryStorage()
                registry = DocumentRegistry(storage, DocumentValidator({"france_chimie": SYNTHETIC_DOMAINS}))
                engine = FranceChimieDocumentSync(registry)
                engine.compare_and_sync((metadata(),), detected_at="2026-07-21")
                event = engine.compare_and_sync(
                    (metadata(**{field_name: value}),),
                    detected_at="2026-07-22",
                )[0]
                self.assertIs(FranceChimieSyncEventType.UPDATED, event.event_type)

    def test_logical_removal_is_emitted_once(self) -> None:
        original = self.first_sync()
        event = self.sync.compare_and_sync((), detected_at="2026-07-22")[0]
        self.assertIs(FranceChimieSyncEventType.REMOVED, event.event_type)
        self.assertEqual(original.document_id, event.document_id)
        self.assertEqual(DocumentStatus.REMOVED.value, event.new_snapshot.status)
        self.assertEqual((), self.sync.compare_and_sync((), detected_at="2026-07-23"))

    def test_redirect_preserves_document_identity(self) -> None:
        original = self.first_sync()
        target = metadata(f"https://{SYNTHETIC_DOMAIN}/publication-b")
        redirect = FranceChimieRedirect.create(
            f"https://{SYNTHETIC_DOMAIN}/publication-a",
            target.canonical_url,
            allowed_domains=SYNTHETIC_DOMAINS,
        )
        event = self.sync.compare_and_sync(
            (target,),
            detected_at="2026-07-22",
            redirects=(redirect,),
        )[0]
        self.assertIs(FranceChimieSyncEventType.REDIRECTED, event.event_type)
        self.assertEqual(original.document_id, event.document_id)
        self.assertEqual(target.canonical_url, event.new_snapshot.canonical_url)

    def test_invalid_redirects_fail_closed(self) -> None:
        self.first_sync()
        target = metadata(f"https://{SYNTHETIC_DOMAIN}/publication-b")
        unknown = FranceChimieRedirect.create(
            f"https://{SYNTHETIC_DOMAIN}/unknown",
            target.canonical_url,
            allowed_domains=SYNTHETIC_DOMAINS,
        )
        missing = FranceChimieRedirect.create(
            f"https://{SYNTHETIC_DOMAIN}/publication-a",
            target.canonical_url,
            allowed_domains=SYNTHETIC_DOMAINS,
        )
        with self.assertRaises(FranceChimieMetadataRefusal):
            self.sync.compare_and_sync((target,), detected_at="2026-07-22", redirects=(unknown,))
        with self.assertRaises(FranceChimieMetadataRefusal):
            self.sync.compare_and_sync((), detected_at="2026-07-22", redirects=(missing,))
        with self.assertRaises(FranceChimieMetadataRefusal):
            FranceChimieRedirect.create(
                f"https://{SYNTHETIC_DOMAIN}/publication-a",
                "https://external.example.invalid/publication-b",
                allowed_domains=SYNTHETIC_DOMAINS,
            )

    def test_events_are_immutable_stable_and_reproducible(self) -> None:
        items = (
            metadata(f"https://{SYNTHETIC_DOMAIN}/z", reference="SYNTHETIC-Z"),
            metadata(f"https://{SYNTHETIC_DOMAIN}/a", reference="SYNTHETIC-A"),
        )
        events = self.sync.compare_and_sync(items, detected_at="2026-07-21")
        self.assertEqual(sorted(item.document_id for item in events), [item.document_id for item in events])
        with self.assertRaises(FrozenInstanceError):
            events[0].detected_at = "2026-07-22"  # type: ignore[misc]
        repeated = self.sync.compare_and_sync(items, detected_at="2026-07-21")
        self.assertTrue(all(event.event_type is FranceChimieSyncEventType.UNCHANGED for event in repeated))

    def test_duplicate_metadata_is_refused(self) -> None:
        item = metadata()
        with self.assertRaises(FranceChimieMetadataRefusal):
            self.sync.compare_and_sync((item, item), detected_at="2026-07-21")

    def test_registry_is_used_through_public_effects(self) -> None:
        self.first_sync()
        documents = self.registry.find_by_connector("france_chimie")
        self.assertEqual(1, len(documents))
        self.assertEqual("france_chimie", documents[0].connector_name)
        self.assertEqual(1, len(self.storage.documents))

    def test_snapshots_and_metadata_are_strictly_content_free(self) -> None:
        event = self.first_sync()
        forbidden = {"attachment", "binary", "body", "content", "excerpt", "full_text", "html", "pdf", "raw_html", "summary", "text"}
        self.assertTrue(forbidden.isdisjoint(field.name for field in fields(FranceChimieMetadata)))
        self.assertTrue(forbidden.isdisjoint(field.name for field in fields(type(event.new_snapshot))))
        self.assertTrue(forbidden.isdisjoint(self.registry.find_by_connector("france_chimie")[0].to_dict()))

    def test_invalid_batches_and_detection_dates_are_refused(self) -> None:
        with self.assertRaises(FranceChimieMetadataRefusal):
            self.sync.compare_and_sync([metadata()], detected_at="2026-07-21")  # type: ignore[arg-type]
        with self.assertRaises(FranceChimieMetadataRefusal):
            self.sync.compare_and_sync((metadata(),), detected_at="invalid")

    def test_sync_module_has_no_network_or_scraping_import(self) -> None:
        forbidden = {"requests", "httpx", "aiohttp", "urllib", "urllib.request", "http.client", "socket", "bs4", "scrapy"}
        path = Path(__file__).with_name("france_chimie_sync.py")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        self.assertTrue(forbidden.isdisjoint(imports))


if __name__ == "__main__":
    unittest.main()
