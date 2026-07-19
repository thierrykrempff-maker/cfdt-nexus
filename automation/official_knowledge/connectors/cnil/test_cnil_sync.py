"""Metadata-only synchronization tests for CNIL LOT 2."""

import ast
import unittest
from dataclasses import replace
from pathlib import Path

from automation.official_knowledge.document_registry import DocumentRecord, DocumentStatus

from .cnil_connector import build_cnil_document_registry
from .cnil_metadata import CnilMetadata, CnilMetadataRefusal
from .cnil_sync import (
    CnilDocumentSync,
    CnilRedirect,
    CnilSyncEvent,
    CnilSyncEventType,
)


class MemoryStorage:
    def __init__(self) -> None:
        self.documents: tuple[DocumentRecord, ...] = ()

    def load(self) -> tuple[DocumentRecord, ...]:
        return self.documents

    def save(self, documents: tuple[DocumentRecord, ...]) -> None:
        self.documents = documents


def metadata(url: str = "https://cnil.fr/fr/publication-a", **changes) -> CnilMetadata:
    values = {
        "canonical_url": url,
        "title": "Publication synthétique",
        "publication_date": "2026-07-01",
        "category": "actualite",
        "family": "actualite",
        "document_type": "actualite",
        "provenance": "cnil",
        "language": "fr",
        "discovered_at": "2026-07-19",
    }
    values.update(changes)
    return CnilMetadata(**values)


class CnilDocumentSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.storage = MemoryStorage()
        self.registry = build_cnil_document_registry(self.storage)
        self.sync = CnilDocumentSync(self.registry)

    def first_sync(self) -> CnilSyncEvent:
        return self.sync.compare_and_sync((metadata(),), detected_at="2026-07-19")[0]

    def test_registry_injection_is_mandatory(self) -> None:
        with self.assertRaisesRegex(CnilMetadataRefusal, "explicitly"):
            CnilDocumentSync(None)  # type: ignore[arg-type]

    def test_new_publication(self) -> None:
        event = self.first_sync()
        self.assertIs(CnilSyncEventType.NEW, event.event_type)
        self.assertEqual("cnil", event.connector_name)
        self.assertIsNone(event.old_value)
        self.assertIsNotNone(event.new_value)

    def test_unchanged_publication(self) -> None:
        self.first_sync()
        event = self.sync.compare_and_sync((metadata(),), detected_at="2026-07-20")[0]
        self.assertIs(CnilSyncEventType.UNCHANGED, event.event_type)
        self.assertEqual(event.old_value.title, event.new_value.title)

    def test_title_update(self) -> None:
        self.first_sync()
        event = self.sync.compare_and_sync((metadata(title="Titre modifié"),), detected_at="2026-07-20")[0]
        self.assertIs(CnilSyncEventType.UPDATED, event.event_type)
        self.assertEqual(("Publication synthétique", "Titre modifié"), (event.old_value.title, event.new_value.title))

    def test_publication_date_update(self) -> None:
        self.first_sync()
        event = self.sync.compare_and_sync((metadata(publication_date="2026-07-02"),), detected_at="2026-07-20")[0]
        self.assertIs(CnilSyncEventType.UPDATED, event.event_type)
        self.assertEqual(("2026-07-01", "2026-07-02"), (event.old_value.publication_date, event.new_value.publication_date))

    def test_category_family_and_document_type_updates(self) -> None:
        for field in ("category", "family", "document_type"):
            with self.subTest(field=field):
                storage = MemoryStorage()
                engine = CnilDocumentSync(build_cnil_document_registry(storage))
                engine.compare_and_sync((metadata(),), detected_at="2026-07-19")
                event = engine.compare_and_sync((metadata(**{field: "guide"}),), detected_at="2026-07-20")[0]
                self.assertIs(CnilSyncEventType.UPDATED, event.event_type)
                self.assertEqual("guide", getattr(event.new_value, field))

    def test_logical_removal(self) -> None:
        first = self.first_sync()
        event = self.sync.compare_and_sync((), detected_at="2026-07-20")[0]
        self.assertIs(CnilSyncEventType.REMOVED, event.event_type)
        self.assertEqual(first.document_id, event.document_id)
        self.assertEqual(DocumentStatus.REMOVED.value, event.new_value.status)
        self.assertEqual(1, len(self.registry.find_removed_documents()))

    def test_already_removed_resource_does_not_emit_again(self) -> None:
        self.first_sync()
        self.sync.compare_and_sync((), detected_at="2026-07-20")
        self.assertEqual((), self.sync.compare_and_sync((), detected_at="2026-07-21"))

    def test_redirect_preserves_document_identity(self) -> None:
        first = self.first_sync()
        target = metadata("https://cnil.fr/fr/publication-b")
        event = self.sync.compare_and_sync(
            (target,),
            detected_at="2026-07-20",
            redirects=(CnilRedirect("https://cnil.fr/fr/publication-a", target.canonical_url),),
        )[0]
        self.assertIs(CnilSyncEventType.REDIRECTED, event.event_type)
        self.assertEqual(first.document_id, event.document_id)
        self.assertEqual("https://cnil.fr/fr/publication-a", event.old_value.canonical_url)
        self.assertEqual("https://cnil.fr/fr/publication-b", event.new_value.canonical_url)

    def test_invalid_redirects_fail_closed(self) -> None:
        self.first_sync()
        target = metadata("https://cnil.fr/fr/publication-b")
        cases = (
            (CnilRedirect("https://cnil.fr/fr/unknown", target.canonical_url),),
            (CnilRedirect("https://cnil.fr/fr/publication-a", target.canonical_url),),
        )
        with self.assertRaisesRegex(CnilMetadataRefusal, "absent"):
            self.sync.compare_and_sync((target,), detected_at="2026-07-20", redirects=cases[0])
        with self.assertRaisesRegex(CnilMetadataRefusal, "target"):
            self.sync.compare_and_sync((), detected_at="2026-07-20", redirects=cases[1])

    def test_events_are_structured_and_deterministic(self) -> None:
        events = self.sync.compare_and_sync(
            (metadata("https://cnil.fr/fr/z"), metadata("https://cnil.fr/fr/a")),
            detected_at="2026-07-19",
        )
        self.assertTrue(all(isinstance(event, CnilSyncEvent) for event in events))
        self.assertEqual(sorted(event.document_id for event in events), [event.document_id for event in events])
        self.assertTrue(all(event.detected_at == "2026-07-19" for event in events))

    def test_duplicate_metadata_and_invalid_date_are_refused(self) -> None:
        item = metadata()
        with self.assertRaisesRegex(CnilMetadataRefusal, "Duplicate"):
            self.sync.compare_and_sync((item, item), detected_at="2026-07-19")
        with self.assertRaisesRegex(CnilMetadataRefusal, "ISO"):
            self.sync.compare_and_sync((item,), detected_at="19/07/2026")

    def test_event_snapshots_have_no_content_fields(self) -> None:
        event = self.first_sync()
        forbidden = {"body", "content", "text", "excerpt", "summary", "html", "pdf", "binary", "attachment"}
        self.assertTrue(forbidden.isdisjoint(event.__dataclass_fields__))
        self.assertTrue(forbidden.isdisjoint(event.new_value.__dataclass_fields__))

    def test_registry_records_remain_metadata_only(self) -> None:
        self.first_sync()
        record = self.registry.find_by_connector("cnil")[0]
        forbidden = {"body", "content", "text", "excerpt", "summary", "html", "pdf", "binary"}
        self.assertTrue(forbidden.isdisjoint(record.to_dict()))

    def test_sync_module_has_no_network_client(self) -> None:
        path = Path(__file__).with_name("cnil_sync.py")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        forbidden = {"requests", "httpx", "aiohttp", "urllib.request", "http.client", "socket"}
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        self.assertTrue(forbidden.isdisjoint(imports))


if __name__ == "__main__":
    unittest.main()
