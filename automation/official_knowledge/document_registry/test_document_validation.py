"""Security, independence and METADATA_ONLY tests for Document Registry."""

from __future__ import annotations

import inspect
from dataclasses import fields, replace

import pytest

from . import (
    DOCUMENT_REGISTRY_POLICY, DocumentRecord, DocumentStatus, DocumentValidationError,
    DocumentValidator, RegistryDocumentPolicy, stable_document_id,
)


CONNECTOR = "official_source"
URL = "https://official.example/item"


def valid_record(**changes):
    values = {
        "document_id": stable_document_id(CONNECTOR, URL), "connector_name": CONNECTOR,
        "canonical_url": URL, "title": "Title", "category": "guidance", "family": "work",
        "document_type": "official_page", "publication_date": None, "first_seen": "2026-07-21",
        "last_checked": "2026-07-21", "last_modified_metadata": "2026-07-21",
        "language": "fr", "provenance": "official_source", "status": DocumentStatus.ACTIVE,
    }
    values.update(changes)
    return DocumentRecord(**values)


def validator():
    return DocumentValidator({CONNECTOR: frozenset({"official.example"})})


def test_document_model_has_only_required_metadata_fields():
    assert tuple(item.name for item in fields(DocumentRecord)) == (
        "document_id", "connector_name", "canonical_url", "title", "category", "family",
        "document_type", "publication_date", "first_seen", "last_checked",
        "last_modified_metadata", "language", "provenance", "status",
    )


def test_stable_identifier_is_deterministic_and_connector_scoped():
    assert stable_document_id(CONNECTOR, URL) == stable_document_id(CONNECTOR, URL)
    assert stable_document_id("other_source", URL) != stable_document_id(CONNECTOR, URL)
    with pytest.raises(DocumentValidationError) as raised:
        validator().validate_new(valid_record(document_id="unstable"))
    assert raised.value.code == "UNSTABLE_DOCUMENT_ID"


@pytest.mark.parametrize(("url", "code"), (
    ("http://official.example/item", "INVALID_URL"),
    ("https://other.example/item", "DOMAIN_NOT_ALLOWED"),
    ("https://official.example/file.pdf", "PDF_FORBIDDEN"),
    ("https://official.example/item#fragment", "INVALID_URL"),
))
def test_https_domain_pdf_and_canonical_guards(url, code):
    with pytest.raises(DocumentValidationError) as raised:
        validator().validate(valid_record(canonical_url=url))
    assert raised.value.code == code


def test_html_and_missing_provenance_are_refused():
    with pytest.raises(DocumentValidationError) as html:
        validator().validate(valid_record(title="<html>content</html>"))
    assert html.value.code == "CONTENT_FORBIDDEN"
    with pytest.raises(DocumentValidationError):
        validator().validate(valid_record(provenance=""))


def test_invalid_timeline_is_refused():
    with pytest.raises(DocumentValidationError) as raised:
        validator().validate(valid_record(last_checked="2026-07-20"))
    assert raised.value.code == "INVALID_TIMELINE"


def test_policy_permanently_forbids_content_cache_and_indexing():
    policy = DOCUMENT_REGISTRY_POLICY
    assert policy.index_level == "METADATA_ONLY"
    assert policy.cache_allowed is False
    assert policy.content_storage_allowed is False
    assert policy.text_indexing_allowed is False
    assert policy.local_document_copy_allowed is False
    assert policy.citation_required and policy.provenance_required
    with pytest.raises(ValueError):
        RegistryDocumentPolicy(content_storage_allowed=True)


def test_production_registry_has_no_connector_dependency():
    import automation.official_knowledge.document_registry.document_models as models
    import automation.official_knowledge.document_registry.document_registry as registry
    import automation.official_knowledge.document_registry.document_validation as validation
    import automation.official_knowledge.document_registry.registry_storage as storage

    source = "\n".join(inspect.getsource(module) for module in (models, registry, validation, storage))
    assert "connectors." not in source
    assert not any(name in source.lower() for name in ("dreets", "cnil", "inrs", "cpam", "carsat"))
    assert not any(token in source for token in ("requests", "urlopen(", "socket.", "httpx"))
