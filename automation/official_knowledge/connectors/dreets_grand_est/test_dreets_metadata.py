"""LOT 3A metadata contract and documentary-policy tests."""

from __future__ import annotations

from dataclasses import fields

import pytest

from .dreets_metadata import (
    ALLOWED_DREETS_DOMAINS,
    LOT_3A_DOCUMENT_POLICY,
    DreetsDocumentPolicy,
    DreetsMetadata,
    DreetsMetadataRefusal,
    canonicalize_public_url,
    validate_metadata_mime_type,
)


def valid_metadata(**changes) -> DreetsMetadata:
    values = {
        "canonical_url": "https://grand-est.dreets.gouv.fr/Travail-et-relations-sociales#section",
        "title": "Travail et relations sociales",
        "date": "2026-07-20",
        "category": "fiche",
        "family": "relations_collectives",
        "document_type": "page_officielle",
        "provenance": "dreets_grand_est",
        "language": "fr",
        "discovered_on": "2026-07-21",
    }
    values.update(changes)
    return DreetsMetadata(**values)


def test_metadata_contains_only_authorized_public_fields():
    metadata = valid_metadata()
    assert tuple(item.name for item in fields(DreetsMetadata)) == (
        "canonical_url", "title", "date", "category", "family", "document_type",
        "provenance", "language", "discovered_on",
    )
    assert set(metadata.to_dict()) == {item.name for item in fields(DreetsMetadata)}
    assert metadata.canonical_url == "https://grand-est.dreets.gouv.fr/Travail-et-relations-sociales"
    assert not any(name in metadata.to_dict() for name in ("text", "excerpt", "html", "pdf", "content"))


def test_allowed_domains_are_exactly_the_lot_2_reviewed_domains():
    assert ALLOWED_DREETS_DOMAINS == frozenset({"grand-est.dreets.gouv.fr", "dreets.gouv.fr"})
    assert canonicalize_public_url("https://dreets.gouv.fr/Mentions-legales") == "https://dreets.gouv.fr/Mentions-legales"


@pytest.mark.parametrize("url", (
    "https://example.org/item",
    "https://facebook.com/dreets",
    "https://sub.grand-est.dreets.gouv.fr/item",
))
def test_third_party_social_and_unreviewed_domains_are_refused(url):
    with pytest.raises(DreetsMetadataRefusal, match="Domain") as raised:
        canonicalize_public_url(url)
    assert raised.value.code == "DOMAIN_NOT_ALLOWED"


@pytest.mark.parametrize("url", (
    "http://grand-est.dreets.gouv.fr/item",
    "not-a-url",
    "https://user:" + "credential" + "@" + "grand-est.dreets.gouv.fr/item",
    "https://grand-est.dreets.gouv.fr:8443/item",
))
def test_invalid_or_non_https_urls_are_refused(url):
    with pytest.raises(DreetsMetadataRefusal) as raised:
        canonicalize_public_url(url)
    assert raised.value.code == "INVALID_URL"


@pytest.mark.parametrize("url", (
    "https://grand-est.dreets.gouv.fr/guide.pdf",
    "https://grand-est.dreets.gouv.fr/IMG/PDF/guide",
    "https://grand-est.dreets.gouv.fr/view?file=guide.pdf",
))
def test_pdf_urls_are_refused(url):
    with pytest.raises(DreetsMetadataRefusal) as raised:
        canonicalize_public_url(url)
    assert raised.value.code == "PDF_FORBIDDEN"


def test_pdf_and_unknown_mime_types_are_refused():
    with pytest.raises(DreetsMetadataRefusal) as pdf:
        validate_metadata_mime_type("application/pdf")
    assert pdf.value.code == "PDF_FORBIDDEN"
    with pytest.raises(DreetsMetadataRefusal) as unknown:
        validate_metadata_mime_type("application/octet-stream")
    assert unknown.value.code == "MIME_NOT_ALLOWED"


def test_metadata_validation_is_fail_closed():
    with pytest.raises(DreetsMetadataRefusal):
        valid_metadata(provenance="unknown")
    with pytest.raises(DreetsMetadataRefusal):
        valid_metadata(title="<html>not metadata</html>")
    with pytest.raises(DreetsMetadataRefusal):
        valid_metadata(discovered_on="today")


def test_document_policy_forbids_every_content_retention_mode():
    policy = LOT_3A_DOCUMENT_POLICY
    assert policy.index_level == "METADATA_ONLY"
    assert policy.cache_allowed is False
    assert policy.text_indexing_allowed is False
    assert policy.local_copy_allowed is False
    assert policy.full_text_allowed is False
    assert policy.excerpts_allowed is False
    assert policy.citation_required is True
    assert policy.provenance_required is True
    with pytest.raises(ValueError):
        DreetsDocumentPolicy(text_indexing_allowed=True)
