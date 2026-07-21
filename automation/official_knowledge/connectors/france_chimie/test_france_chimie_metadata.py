"""Offline metadata validation tests for France Chimie."""

import unittest
from dataclasses import fields

from automation.official_knowledge.document_registry import DocumentRecord, DocumentStatus, DocumentValidator, stable_document_id

from .france_chimie_catalog import FRANCE_CHIMIE_ACTIVE_DOMAINS
from .france_chimie_contract import FranceChimieConnector
from .france_chimie_metadata import (
    FranceChimieMetadata,
    FranceChimieMetadataRefusal,
    metadata_from_mapping,
    normalize_injected_metadata,
)


SYNTHETIC_DOMAIN = "france-chimie.example.invalid"
SYNTHETIC_DOMAINS = frozenset({SYNTHETIC_DOMAIN})


def synthetic(**changes):
    value = {
        "url": f"https://{SYNTHETIC_DOMAIN}/publications/fiche-a",
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
    return value


class FranceChimieMetadataTests(unittest.TestCase):
    def test_local_injected_metadata_is_normalized(self) -> None:
        item = metadata_from_mapping(synthetic(), allowed_domains=SYNTHETIC_DOMAINS)
        self.assertEqual("france_chimie", item.connector_name)
        self.assertTrue(item.metadata_only)
        self.assertEqual("france_chimie", item.provenance)
        self.assertEqual(
            stable_document_id("france_chimie", item.canonical_url),
            item.document_id,
        )

    def test_declared_official_domains_are_not_activated(self) -> None:
        self.assertEqual(frozenset(), FRANCE_CHIMIE_ACTIVE_DOMAINS)
        with self.assertRaisesRegex(FranceChimieMetadataRefusal, "No France Chimie domain is activated"):
            metadata_from_mapping(synthetic(), allowed_domains=FRANCE_CHIMIE_ACTIVE_DOMAINS)

    def test_connector_accepts_only_explicit_local_configuration(self) -> None:
        connector = FranceChimieConnector()
        with self.assertRaises(FranceChimieMetadataRefusal):
            connector.validate_injected_metadata((synthetic(),))
        result = connector.validate_injected_metadata((synthetic(),), allowed_domains=SYNTHETIC_DOMAINS)
        self.assertEqual(1, len(result))

    def test_document_registry_compatibility(self) -> None:
        item = metadata_from_mapping(synthetic(), allowed_domains=SYNTHETIC_DOMAINS)
        record = DocumentRecord(
            **item.to_registry_fields(),
            first_seen=item.discovered_at,
            last_checked=item.discovered_at,
            last_modified_metadata=item.discovered_at,
            status=DocumentStatus.ACTIVE,
        )
        DocumentValidator({"france_chimie": SYNTHETIC_DOMAINS}).validate_new(record)

    def test_https_domain_fragment_and_pdf_guards(self) -> None:
        invalid = (
            "http://france-chimie.example.invalid/item",
            "https://external.example.invalid/item",
            "https://france-chimie.example.invalid/item#fragment",
            "https://france-chimie.example.invalid/item.pdf",
            "https://france-chimie.example.invalid/pdf/item",
        )
        for url in invalid:
            with self.subTest(url=url):
                with self.assertRaises(FranceChimieMetadataRefusal):
                    metadata_from_mapping(synthetic(url=url), allowed_domains=SYNTHETIC_DOMAINS)

    def test_content_html_binary_and_unknown_fields_are_refused(self) -> None:
        for field_name, value in (
            ("content", "forbidden"),
            ("full_text", "forbidden"),
            ("html", "<p>forbidden</p>"),
            ("summary", "unknown and forbidden by default"),
            ("payload", b"binary"),
        ):
            with self.subTest(field=field_name):
                with self.assertRaises(FranceChimieMetadataRefusal):
                    metadata_from_mapping(synthetic(**{field_name: value}), allowed_domains=SYNTHETIC_DOMAINS)
        with self.assertRaises(FranceChimieMetadataRefusal):
            metadata_from_mapping(synthetic(title="<p>HTML</p>"), allowed_domains=SYNTHETIC_DOMAINS)

    def test_model_has_no_content_field(self) -> None:
        forbidden = {"attachment", "binary", "body", "content", "excerpt", "full_text", "html", "pdf", "raw_html", "summary", "text"}
        self.assertTrue(forbidden.isdisjoint(field.name for field in fields(FranceChimieMetadata)))

    def test_batch_is_bounded_deduplicated_and_deterministic(self) -> None:
        first = synthetic(url=f"https://{SYNTHETIC_DOMAIN}/z")
        second = synthetic(url=f"https://{SYNTHETIC_DOMAIN}/a", reference="SYNTHETIC-002")
        ordered = normalize_injected_metadata((first, second), allowed_domains=SYNTHETIC_DOMAINS)
        self.assertEqual(sorted(item.canonical_url for item in ordered), [item.canonical_url for item in ordered])
        self.assertEqual(1, len(normalize_injected_metadata((first, first), allowed_domains=SYNTHETIC_DOMAINS)))
        with self.assertRaises(FranceChimieMetadataRefusal):
            normalize_injected_metadata((first,), allowed_domains=SYNTHETIC_DOMAINS, limit=0)

    def test_conflicting_duplicate_is_refused(self) -> None:
        with self.assertRaisesRegex(FranceChimieMetadataRefusal, "Conflicting metadata"):
            normalize_injected_metadata(
                (synthetic(), synthetic(title="Titre contradictoire")),
                allowed_domains=SYNTHETIC_DOMAINS,
            )

    def test_query_canonicalization_is_deterministic(self) -> None:
        first = metadata_from_mapping(
            synthetic(url=f"https://{SYNTHETIC_DOMAIN}/item?b=2&a=1"),
            allowed_domains=SYNTHETIC_DOMAINS,
        )
        second = metadata_from_mapping(
            synthetic(url=f"https://{SYNTHETIC_DOMAIN}/item?a=1&b=2"),
            allowed_domains=SYNTHETIC_DOMAINS,
        )
        self.assertEqual(first.canonical_url, second.canonical_url)
        self.assertEqual(first.document_id, second.document_id)

    def test_dates_and_taxonomy_fail_closed(self) -> None:
        for changes in (
            {"publication_date": "21/07/2026"},
            {"discovered_at": "invalid"},
            {"family": "invented"},
            {"document_type": "invented"},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(FranceChimieMetadataRefusal):
                    metadata_from_mapping(synthetic(**changes), allowed_domains=SYNTHETIC_DOMAINS)


if __name__ == "__main__":
    unittest.main()
