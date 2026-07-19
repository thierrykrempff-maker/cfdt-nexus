import ast
import unittest
from dataclasses import fields
from pathlib import Path

from automation.official_knowledge.document_registry import DocumentRecord, DocumentStatus, DocumentValidator, stable_document_id

from .inrs_connector import InrsConnector
from .inrs_metadata import (
    INRS_SOURCE_DOMAIN,
    InrsMetadata,
    InrsMetadataDocumentType,
    InrsMetadataFamily,
    InrsMetadataRefusal,
    canonicalize_inrs_url,
    metadata_from_mapping,
    stable_inrs_document_id,
)


def synthetic(**overrides):
    value = {
        "url": "https://www.inrs.fr/publications/ed-0000?utm_source=test#section",
        "title": "Brochure synthétique",
        "document_type": "brochure",
        "category": "prévention",
        "family": "risques_chimiques",
        "publication_date": "2026-01-02",
        "last_modified_date": "2026-02-03",
        "language": "fr",
        "discovered_at": "2026-03-04",
        "reference": "ED 0000",
        "keywords": ("synthétique", "prévention"),
        "summary": "Résumé synthétique court.",
    }
    value.update(overrides)
    return value


class RegistrySpy:
    def __init__(self):
        self.calls = []

    def register_document(self, document):
        self.calls.append(("register", document))

    def update_document(self, document):
        self.calls.append(("update", document))

    def find_document(self, document_id):
        self.calls.append(("find", document_id))


class InrsMetadataDiscoveryTests(unittest.TestCase):
    def test_connector_disabled_by_default(self):
        with self.assertRaisesRegex(InrsMetadataRefusal, "disabled"):
            InrsConnector().discover_metadata((synthetic(),))

    def test_activation_is_explicit_and_boolean(self):
        connector = InrsConnector().activate_metadata_discovery()
        self.assertTrue(connector.enabled)
        self.assertEqual(1, len(connector.discover_metadata((synthetic(),))))
        with self.assertRaises(TypeError):
            InrsConnector(enabled=1)

    def test_offline_injected_discovery(self):
        result = InrsConnector(enabled=True).discover_metadata((synthetic(),))[0]
        self.assertIsInstance(result, InrsMetadata)
        self.assertEqual(("inrs", "INRS", INRS_SOURCE_DOMAIN), (result.connector_name, result.source_name, result.source_domain))
        self.assertTrue(result.metadata_only)

    def test_stable_id_uses_common_registry_identity(self):
        first = metadata_from_mapping(synthetic(url="https://www.inrs.fr/a"))
        second = metadata_from_mapping(synthetic(url="https://www.inrs.fr/b"))
        self.assertNotEqual(first.document_id, second.document_id)
        self.assertEqual(first.document_id, stable_inrs_document_id(first.canonical_url, "ED-0000"))
        self.assertEqual(first.document_id, stable_document_id("inrs", first.canonical_url))
        self.assertEqual("ED 0000", first.reference)

    def test_stable_id_falls_back_to_canonical_url(self):
        first = metadata_from_mapping(synthetic(reference=None, url="https://www.inrs.fr/a#one"))
        second = metadata_from_mapping(synthetic(reference=None, url="https://www.inrs.fr/a#two"))
        self.assertEqual(first.document_id, second.document_id)

    def test_url_normalization(self):
        value = canonicalize_inrs_url("HTTPS://WWW.INRS.FR//publications/item/?utm_source=x&id=2&refINRS=ED1#part")
        self.assertEqual("https://www.inrs.fr/publications/item?id=2&refinrs=ED1", value)

    def test_external_domain_rejected(self):
        with self.assertRaisesRegex(InrsMetadataRefusal, "allowed INRS"):
            metadata_from_mapping(synthetic(url="https://example.org/publication"))

    def test_invalid_and_empty_urls_rejected(self):
        for value in ("", "http://www.inrs.fr/a", "https://www.inrs.fr.evil.test/a"):
            with self.subTest(value=value), self.assertRaises(InrsMetadataRefusal):
                metadata_from_mapping(synthetic(url=value))

    def test_type_aliases_are_normalized(self):
        self.assertIs(InrsMetadataDocumentType.FICHE_PRATIQUE, metadata_from_mapping(synthetic(document_type="fiche")).document_type)
        self.assertIs(InrsMetadataDocumentType.DOSSIER_WEB, metadata_from_mapping(synthetic(document_type="dossier")).document_type)

    def test_unknown_type_is_rejected(self):
        with self.assertRaisesRegex(InrsMetadataRefusal, "Unknown document type"):
            metadata_from_mapping(synthetic(document_type="mystere"))

    def test_family_aliases_and_fallback(self):
        self.assertIs(InrsMetadataFamily.RISQUES_PSYCHOSOCIAUX, metadata_from_mapping(synthetic(family="RPS")).family)
        self.assertIs(InrsMetadataFamily.AUTRE, metadata_from_mapping(synthetic(family="incertain")).family)

    def test_missing_dates_are_accepted(self):
        value = metadata_from_mapping(synthetic(publication_date=None, last_modified_date=None))
        self.assertIsNone(value.publication_date)
        self.assertIsNone(value.last_modified_date)

    def test_invalid_dates_are_rejected(self):
        for field_name in ("publication_date", "last_modified_date", "discovered_at"):
            with self.subTest(field=field_name), self.assertRaises(InrsMetadataRefusal):
                metadata_from_mapping(synthetic(**{field_name: "31/12/2026"}))

    def test_html_and_long_text_are_rejected(self):
        for override in ({"title": "<h1>titre</h1>"}, {"summary": "<p>contenu</p>"}, {"summary": "x" * 501}):
            with self.subTest(override=override), self.assertRaises(InrsMetadataRefusal):
                metadata_from_mapping(synthetic(**override))

    def test_binary_is_rejected_recursively(self):
        with self.assertRaisesRegex(InrsMetadataRefusal, "Binary"):
            metadata_from_mapping(synthetic(keywords=(b"binary",)))

    def test_content_fields_are_rejected(self):
        for field_name in ("content", "full_text", "html", "pdf", "body", "raw_html"):
            with self.subTest(field=field_name), self.assertRaisesRegex(InrsMetadataRefusal, "content fields"):
                metadata_from_mapping(synthetic(**{field_name: "forbidden"}))

    def test_pdf_url_is_rejected(self):
        with self.assertRaisesRegex(InrsMetadataRefusal, "PDF"):
            metadata_from_mapping(synthetic(url="https://www.inrs.fr/media/document.pdf"))

    def test_order_is_deterministic(self):
        connector = InrsConnector(enabled=True)
        first = synthetic(reference="ED 1", url="https://www.inrs.fr/z")
        second = synthetic(reference="ED 2", url="https://www.inrs.fr/a")
        self.assertEqual(connector.discover_metadata((first, second)), connector.discover_metadata((second, first)))

    def test_identical_references_are_deduplicated(self):
        item = synthetic()
        self.assertEqual(1, len(InrsConnector(enabled=True).discover_metadata((item, dict(item)))))

    def test_conflicting_duplicate_is_rejected(self):
        with self.assertRaisesRegex(InrsMetadataRefusal, "Conflicting"):
            InrsConnector(enabled=True).discover_metadata((synthetic(), synthetic(title="Autre titre")))

    def test_registry_structural_compatibility(self):
        metadata = metadata_from_mapping(synthetic(reference=None))
        record = DocumentRecord(
            **metadata.to_registry_fields(), first_seen=metadata.discovered_at,
            last_checked=metadata.discovered_at, last_modified_metadata=metadata.discovered_at,
            status=DocumentStatus.ACTIVE,
        )
        DocumentValidator({"inrs": frozenset({INRS_SOURCE_DOMAIN})}).validate(record)

    def test_discovery_never_writes_registry(self):
        registry = RegistrySpy()
        connector = InrsConnector(document_registry=registry, enabled=True)
        connector.discover_metadata((synthetic(),))
        self.assertEqual([], registry.calls)

    def test_model_has_no_document_content_field(self):
        names = {field.name for field in fields(InrsMetadata)}
        self.assertTrue({"document_id", "canonical_url", "summary", "metadata_only"} <= names)
        self.assertTrue({"content", "full_text", "html", "pdf", "body"}.isdisjoint(names))

    def test_no_network_or_download_import(self):
        forbidden = {"requests", "httpx", "aiohttp", "urllib", "urllib.request", "http.client", "socket"}
        for path in Path(__file__).parent.glob("*.py"):
            if path.name.startswith("test_"):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module)
            self.assertTrue(forbidden.isdisjoint(imports), path.name)

    def test_limit_is_bounded(self):
        with self.assertRaises(ValueError):
            InrsConnector(enabled=True, limit=101)
        with self.assertRaisesRegex(InrsMetadataRefusal, "limit exceeded"):
            InrsConnector(enabled=True, limit=1).discover_metadata((synthetic(reference="ED 1"), synthetic(reference="ED 2")))


if __name__ == "__main__":
    unittest.main()
