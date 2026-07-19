"""Validation tests for the exclusive CNIL metadata contract."""

import unittest

from .cnil_metadata import (
    CNIL_METADATA_MIME_TYPES,
    CnilMetadata,
    CnilMetadataRefusal,
    CnilTaxonomy,
    canonicalize_cnil_url,
    validate_cnil_mime_type,
)


def metadata(**changes) -> CnilMetadata:
    values = {
        "canonical_url": "https://cnil.fr/fr/actualite-synthetique",
        "title": "Actualité synthétique",
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


class CnilMetadataTests(unittest.TestCase):
    def test_valid_metadata_and_exact_fields(self) -> None:
        value = metadata()
        self.assertEqual("https://cnil.fr/fr/actualite-synthetique", value.canonical_url)
        self.assertEqual(
            {
                "canonical_url", "title", "publication_date", "category", "family",
                "document_type", "provenance", "language", "discovered_at",
            },
            set(value.to_dict()),
        )

    def test_serialization_is_deterministic(self) -> None:
        self.assertEqual(metadata().to_dict(), metadata().to_dict())
        self.assertEqual("actualite", metadata().to_dict()["category"])

    def test_www_is_documented_canonical_alias(self) -> None:
        self.assertEqual(
            "https://cnil.fr/fr/guide?source=lot1",
            canonicalize_cnil_url("https://www.cnil.fr/fr/guide?source=lot1"),
        )

    def test_plain_official_url_is_valid(self) -> None:
        self.assertEqual("https://cnil.fr/", canonicalize_cnil_url("https://cnil.fr"))

    def test_https_is_required(self) -> None:
        with self.assertRaisesRegex(CnilMetadataRefusal, "HTTPS"):
            canonicalize_cnil_url("http://cnil.fr/fr/test")

    def test_third_party_and_lookalike_domains_are_refused(self) -> None:
        for value in (
            "https://evil.example/test",
            "https://evil-cnil.fr/test",
            "https://cnil.fr.evil.example/test",
            "https://social.example/test",
        ):
            with self.subTest(value=value), self.assertRaises(CnilMetadataRefusal):
                canonicalize_cnil_url(value)

    def test_unapproved_subdomain_is_refused(self) -> None:
        with self.assertRaisesRegex(CnilMetadataRefusal, "cnil.fr"):
            canonicalize_cnil_url("https://linc.cnil.fr/test")

    def test_credentials_port_and_fragment_are_refused(self) -> None:
        for value in (
            "https://synthetic-user:synthetic-credential" "@cnil.fr/test",
            "https://cnil.fr:8443/test",
            "https://cnil.fr/test#fragment",
        ):
            with self.subTest(value=value), self.assertRaises(CnilMetadataRefusal):
                canonicalize_cnil_url(value)

    def test_malformed_and_other_schemes_are_refused(self) -> None:
        for value in ("not a url", "ftp://cnil.fr/test", "https://[bad/test"):
            with self.subTest(value=value), self.assertRaises(CnilMetadataRefusal):
                canonicalize_cnil_url(value)

    def test_pdf_is_refused_by_url(self) -> None:
        for value in ("https://cnil.fr/file.pdf", "https://cnil.fr/file.PDF?x=1", "https://cnil.fr/pdf/file"):
            with self.subTest(value=value), self.assertRaisesRegex(CnilMetadataRefusal, "PDF"):
                canonicalize_cnil_url(value)

    def test_allowed_mime_types(self) -> None:
        self.assertEqual(
            {"text/html", "application/rss+xml", "application/atom+xml"},
            set(CNIL_METADATA_MIME_TYPES),
        )
        for value in CNIL_METADATA_MIME_TYPES:
            self.assertEqual(value, validate_cnil_mime_type(value))

    def test_pdf_and_other_mime_types_are_refused(self) -> None:
        for value in ("application/pdf", "application/octet-stream", "text/plain", "application/json"):
            with self.subTest(value=value), self.assertRaises(CnilMetadataRefusal):
                validate_cnil_mime_type(value)

    def test_empty_or_html_title_is_refused(self) -> None:
        for title in ("", "   ", "<b>Titre</b>"):
            with self.subTest(title=title), self.assertRaises(CnilMetadataRefusal):
                metadata(title=title)

    def test_invalid_dates_are_refused(self) -> None:
        for changes in ({"publication_date": "19/07/2026"}, {"discovered_at": "2026-13-01"}):
            with self.subTest(changes=changes), self.assertRaises(CnilMetadataRefusal):
                metadata(**changes)

    def test_provenance_and_language_are_required(self) -> None:
        for changes in ({"provenance": ""}, {"provenance": "external"}, {"language": ""}):
            with self.subTest(changes=changes), self.assertRaises(CnilMetadataRefusal):
                metadata(**changes)

    def test_unknown_taxonomy_is_refused(self) -> None:
        for name in ("category", "family", "document_type"):
            with self.subTest(name=name), self.assertRaisesRegex(CnilMetadataRefusal, "Unknown"):
                metadata(**{name: "unknown"})

    def test_taxonomy_is_closed_and_complete(self) -> None:
        self.assertEqual(
            {
                "actualite", "deliberation", "recommandation", "guide",
                "fiche_pratique", "sanction", "referentiel", "faq",
                "autre_publication_publique",
            },
            {item.value for item in CnilTaxonomy},
        )


if __name__ == "__main__":
    unittest.main()
