"""Offline tests for the ANACT metadata synchronization engine."""

import ast
import unittest
from pathlib import Path

from automation.official_knowledge.document_registry import (
    DocumentRecord,
    DocumentStatus,
    DocumentValidator,
    stable_document_id,
)

from .anact_models import (
    AnactResource,
    AnactResourceType,
    AnactTheme,
    GeographicScope,
)
from .anact_sync import (
    AnactDocumentSnapshot,
    AnactDocumentSync,
    AnactRedirect,
    AnactSyncError,
    AnactSyncEventType,
)


DETECTED_AT = "2026-07-21"


def resource(
    suffix: str = "guide-qvct",
    *,
    reference: str = "ANACT-SYNTHETIC-001",
    title: str = "Guide QVCT synthétique",
    published_at: str | None = "2026-07-01",
    theme: AnactTheme = AnactTheme.QVCT,
    resource_type: AnactResourceType = AnactResourceType.GUIDE,
) -> AnactResource:
    return AnactResource(
        reference,
        "anact_national",
        resource_type,
        theme,
        title,
        f"https://example.invalid/anact/{suffix}",
        published_at=published_at,
        scope=GeographicScope.NATIONAL,
        synthetic_only=True,
        official_content=False,
    )


def events(
    previous: tuple[AnactResource, ...],
    current: tuple[AnactResource, ...],
    *,
    redirects: tuple[AnactRedirect, ...] = (),
):
    return AnactDocumentSync().compare_inventories(
        previous,
        current,
        detected_at=DETECTED_AT,
        redirects=redirects,
    )


class AnactDocumentSyncTests(unittest.TestCase):
    def test_identity_uses_common_stable_document_id(self) -> None:
        value = resource()
        self.assertEqual(stable_document_id("anact", value.canonical_url), value.document_id)
        self.assertEqual(value.document_id, events((), (value,))[0].document_id)

    def test_new_document(self) -> None:
        event = events((), (resource(),))[0]
        self.assertIs(AnactSyncEventType.NEW, event.event_type)
        self.assertIsNone(event.previous_snapshot)
        self.assertIsNotNone(event.new_snapshot)

    def test_title_change_is_updated(self) -> None:
        event = events((resource(),), (resource(title="Titre modifié"),))[0]
        self.assertIs(AnactSyncEventType.UPDATED, event.event_type)
        self.assertIn("title", event.changed_fields)

    def test_publication_date_change_is_updated(self) -> None:
        event = events((resource(),), (resource(published_at="2026-07-15"),))[0]
        self.assertIs(AnactSyncEventType.UPDATED, event.event_type)
        self.assertIn("publication_date", event.changed_fields)

    def test_metadata_hash_change_is_updated(self) -> None:
        event = events((resource(),), (resource(reference="ANACT-SYNTHETIC-002"),))[0]
        self.assertIs(AnactSyncEventType.UPDATED, event.event_type)
        self.assertIn("metadata_hash", event.changed_fields)

    def test_removed_document(self) -> None:
        event = events((resource(),), ())[0]
        self.assertIs(AnactSyncEventType.REMOVED, event.event_type)
        self.assertIs(DocumentStatus.REMOVED, event.new_snapshot.status)

    def test_unchanged_document(self) -> None:
        event = events((resource(),), (resource(),))[0]
        self.assertIs(AnactSyncEventType.UNCHANGED, event.event_type)
        self.assertEqual((), event.changed_fields)

    def test_changed_url_without_redirect_is_new_and_removed(self) -> None:
        result = events((resource("old"),), (resource("new"),))
        self.assertEqual(
            {AnactSyncEventType.NEW, AnactSyncEventType.REMOVED},
            {item.event_type for item in result},
        )

    def test_redirect_preserves_registry_identity(self) -> None:
        previous = resource("old")
        current = resource("new")
        event = events(
            (previous,),
            (current,),
            redirects=(AnactRedirect(previous.canonical_url, current.canonical_url),),
        )[0]
        self.assertIs(AnactSyncEventType.REDIRECTED, event.event_type)
        self.assertEqual(previous.document_id, event.document_id)
        self.assertEqual(previous.document_id, event.new_snapshot.document_id)
        self.assertIn("canonical_url", event.changed_fields)

    def test_duplicate_canonical_url_is_refused(self) -> None:
        with self.assertRaisesRegex(AnactSyncError, "Duplicate ANACT canonical URL") as raised:
            events((), (resource(), resource(reference="ANACT-SYNTHETIC-002")))
        self.assertEqual("DUPLICATE_DOCUMENT", raised.exception.code)

    def test_output_is_deterministic_and_stably_sorted(self) -> None:
        current = (resource("z"), resource("a"))
        first = events((), current)
        second = events((), tuple(reversed(current)))
        self.assertEqual(first, second)
        self.assertEqual(tuple(sorted(item.document_id for item in first)), tuple(item.document_id for item in first))

    def test_snapshot_is_document_registry_compatible(self) -> None:
        snapshot = AnactDocumentSnapshot.from_resource(resource())
        record = snapshot.to_document_record(checked_on=DETECTED_AT)
        self.assertIsInstance(record, DocumentRecord)
        DocumentValidator({"anact": frozenset({"example.invalid"})}).validate_new(record)

    def test_sync_module_has_no_network_scraping_or_download_dependency(self) -> None:
        path = Path(__file__).with_name("anact_sync.py")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        forbidden = {
            "aiohttp",
            "bs4",
            "html.parser",
            "http.client",
            "requests",
            "scrapy",
            "socket",
            "ssl",
            "urllib",
            "urllib.request",
            "xml.etree.ElementTree",
        }
        self.assertTrue(forbidden.isdisjoint(imports))
        source = path.read_text(encoding="utf-8").lower()
        for primitive in ("urlopen", "httpclient", "htmlparser", "elementtree", "download(", "scrape("):
            self.assertNotIn(primitive, source)


if __name__ == "__main__":
    unittest.main()
