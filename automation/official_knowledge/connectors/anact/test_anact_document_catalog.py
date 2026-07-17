import inspect
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_license import LicenseId

from .anact_classification_models import HumanValidationStatus
from .anact_contract import AnactConnector
from .anact_document_catalog import InMemoryAnactDocumentCatalog
from .anact_document_catalog_models import CatalogChange, CatalogDocument, CatalogLifecycle, CatalogQuery
from .anact_page_metadata_models import PageMetadata
from .anact_url_classifier import AnactUrlClassifier


NOW = datetime(2026, 7, 19, tzinfo=timezone.utc)


def classification(url="https://www.anact.fr/guides/qvct"):
    return AnactUrlClassifier().classify_url(url)


def metadata(value=None, *, title="Guide QVCT", description="Améliorer les conditions de travail.", canonical=None, final=None, etag='"v1"', published="2026-07-01", updated="2026-07-17", language="fr"):
    value = value or classification()
    requested = value.normalized_url
    final = final or requested
    canonical = canonical or final
    return PageMetadata(
        requested,
        final,
        canonical,
        title,
        description,
        language,
        published,
        updated,
        "article",
        (),
        (),
        etag,
        "Thu, 17 Jul 2026 12:00:00 GMT",
        "text/html",
        1234,
        value.fingerprint,
        value.category.value,
        value.region_id,
        NOW,
    )


def record(value=None, **kwargs):
    value = value or classification()
    return CatalogDocument.from_metadata(metadata(value, **kwargs), value)


class AnactDocumentCatalogTests(unittest.TestCase):
    def test_creates_normalized_record(self):
        value = record()
        self.assertEqual(("guide", "fr", "Guide QVCT", "text/html"), (value.category, value.language, value.title, value.mime_type))
        self.assertEqual("https://www.anact.fr/sitemap.xml", value.discovery_source)

    def test_stable_identifier(self): self.assertEqual(record().document_id, record().document_id)

    def test_policy_and_license_are_preserved(self):
        value = record()
        self.assertEqual((DocumentPolicy.METADATA_ONLY.value, LicenseId.DOCUMENT_SPECIFIC.value), (value.document_policy, value.license_id))

    def test_classification_mismatch_is_rejected(self):
        first = classification(); second = classification("https://www.anact.fr/actualites/x")
        with self.assertRaisesRegex(ValueError, "classification_fingerprint_mismatch"): CatalogDocument.from_metadata(metadata(first), second)

    def test_human_validation_is_required(self):
        value = classification("https://www.anact.fr/ressource/guide-qvct")
        with self.assertRaisesRegex(ValueError, "human_validation_required"): CatalogDocument.from_metadata(metadata(value), value)
        accepted = CatalogDocument.from_metadata(metadata(value), value, human_status=HumanValidationStatus.ACCEPTED)
        self.assertEqual("accepted", accepted.human_validation_status)

    def test_no_fulltext_field(self): self.assertFalse(hasattr(record(), "fulltext"))

    def test_upsert_new(self):
        event = InMemoryAnactDocumentCatalog().upsert(record())
        self.assertIs(CatalogChange.NEW, event.change)
        self.assertIsNotNone(event.version)

    def test_upsert_unchanged(self):
        catalog = InMemoryAnactDocumentCatalog(); catalog.upsert(record())
        event = catalog.upsert(record())
        self.assertIs(CatalogChange.UNCHANGED, event.change)
        self.assertIsNone(event.version)

    def test_modified_metadata_creates_version(self):
        catalog = InMemoryAnactDocumentCatalog(); first = record(); catalog.upsert(first)
        event = catalog.upsert(record(title="Nouveau titre", etag='"v2"'))
        self.assertIs(CatalogChange.MODIFIED, event.change)
        self.assertEqual(2, len(catalog.versions(first.document_id)))

    def test_disappearance_is_detected_without_deletion(self):
        catalog = InMemoryAnactDocumentCatalog(); first = record(); catalog.reconcile((first,))
        event = catalog.reconcile(())[0]
        self.assertIs(CatalogChange.DISAPPEARED, event.change)
        self.assertIs(CatalogLifecycle.DISAPPEARED, catalog.get(first.document_id).lifecycle)

    def test_redirect_alias_deduplicates(self):
        catalog = InMemoryAnactDocumentCatalog()
        old = record(canonical="https://www.anact.fr/guides/qvct", final="https://www.anact.fr/guides/qvct")
        redirected = record(canonical="https://www.anact.fr/guides/qvct", final="https://www.anact.fr/guides/qvct-v2")
        catalog.upsert(old); catalog.upsert(redirected)
        self.assertEqual(1, len(catalog.records()))
        self.assertIn("https://www.anact.fr/guides/qvct-v2", catalog.records()[0].aliases)

    def test_new_canonical_from_known_redirect_preserves_identifier(self):
        catalog = InMemoryAnactDocumentCatalog()
        old = record(canonical="https://www.anact.fr/guides/qvct")
        catalog.upsert(old)
        redirected = record(canonical="https://www.anact.fr/guides/qvct-v2", final="https://www.anact.fr/guides/qvct-v2")
        event = catalog.upsert(redirected)
        self.assertEqual(old.document_id, event.document.document_id)
        self.assertEqual(1, len(catalog.records()))

    def test_canonical_deduplicates(self):
        catalog = InMemoryAnactDocumentCatalog(); first = record(); second = record(title="Guide révisé")
        catalog.reconcile((first, second))
        self.assertEqual(1, len(catalog.records()))

    def test_reconcile_is_order_deterministic(self):
        first = record(); second = record(title="Guide révisé", etag='"v2"')
        left = InMemoryAnactDocumentCatalog(); right = InMemoryAnactDocumentCatalog()
        left.reconcile((first, second)); right.reconcile((second, first))
        self.assertEqual(left.export(), right.export())

    def test_search_by_category(self):
        catalog = InMemoryAnactDocumentCatalog(); catalog.upsert(record())
        self.assertEqual(1, len(catalog.search(CatalogQuery(category="guide"))))
        self.assertFalse(catalog.search(CatalogQuery(category="news")))

    def test_search_by_region(self):
        value = classification("https://www.anact.fr/grand-est/ressource")
        catalog = InMemoryAnactDocumentCatalog(); catalog.upsert(record(value))
        self.assertEqual(1, len(catalog.search(CatalogQuery(region_id="grand_est"))))

    def test_search_by_language(self):
        catalog = InMemoryAnactDocumentCatalog(); catalog.upsert(record())
        self.assertEqual(1, len(catalog.search(CatalogQuery(language="fr"))))

    def test_search_by_lifecycle(self):
        catalog = InMemoryAnactDocumentCatalog(); catalog.reconcile((record(),)); catalog.reconcile(())
        self.assertEqual(1, len(catalog.search(CatalogQuery(lifecycle=CatalogLifecycle.DISAPPEARED))))

    def test_search_by_validation(self):
        catalog = InMemoryAnactDocumentCatalog(); catalog.upsert(record())
        query = CatalogQuery(validation_decision="auto_accepted", human_validation_status="not_required")
        self.assertEqual(1, len(catalog.search(query)))

    def test_search_by_date(self):
        catalog = InMemoryAnactDocumentCatalog(); catalog.upsert(record())
        self.assertEqual(1, len(catalog.search(CatalogQuery(date_from="2026-07-15", date_to="2026-07-20"))))
        self.assertFalse(catalog.search(CatalogQuery(date_from="2027-01-01")))

    def test_search_dates_support_timezones(self):
        catalog = InMemoryAnactDocumentCatalog(); catalog.upsert(record(published="2026-07-01T10:00:00Z"))
        self.assertEqual(1, len(catalog.search(CatalogQuery(date_from="2026-07-01T09:00:00+00:00"))))

    def test_invalid_search_date_is_rejected(self):
        catalog = InMemoryAnactDocumentCatalog(); catalog.upsert(record())
        with self.assertRaisesRegex(ValueError, "invalid date_from"): catalog.search(CatalogQuery(date_from="invalid"))

    def test_search_title_case_insensitive(self):
        catalog = InMemoryAnactDocumentCatalog(); catalog.upsert(record())
        self.assertEqual(1, len(catalog.search(CatalogQuery(title_term="qvct"))))

    def test_search_description_only(self):
        catalog = InMemoryAnactDocumentCatalog(); catalog.upsert(record())
        self.assertEqual(1, len(catalog.search(CatalogQuery(description_term="CONDITIONS"))))
        self.assertFalse(catalog.search(CatalogQuery(description_term="corps intégral")))

    def test_export_is_internal_and_sorted(self):
        catalog = InMemoryAnactDocumentCatalog(); catalog.upsert(record())
        exported = catalog.export()
        self.assertEqual("anact-document-catalog-v1", exported.schema_version)
        self.assertEqual(1, len(exported.records)); self.assertEqual(1, len(exported.versions))

    def test_versions_link_to_previous(self):
        catalog = InMemoryAnactDocumentCatalog(); first = record(); catalog.upsert(first); catalog.upsert(record(title="Révision"))
        versions = catalog.versions(first.document_id)
        self.assertEqual(versions[0].version_id, versions[1].previous_version_id)

    def test_connector_creates_empty_catalog(self): self.assertFalse(AnactConnector().new_document_catalog().records())

    def test_catalog_has_no_network_or_persistence(self):
        from . import anact_document_catalog as module
        source = inspect.getsource(module)
        for primitive in ("urlopen", "requests", "httpx", "open(", "write_text", "write_bytes", "sqlite"):
            self.assertNotIn(primitive, source)


if __name__ == "__main__":
    unittest.main()
