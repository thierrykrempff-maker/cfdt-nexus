import json

import pytest

from DOCUMENT_INTELLIGENCE_CENTER import (
    DocumentKind,
    DocumentMetadataInput,
    MetadataStatus,
)


def _input(**changes) -> DocumentMetadataInput:
    values = {
        "pseudonymous_id": "document-12345678",
        "document_kind": DocumentKind.OTHER,
        "normalized_title": "Document synthétique",
        "logical_provenance": "SYNTHETIC_METADATA",
        "document_date": "2026-07-23",
        "status": MetadataStatus.ACTIVE,
        "topics": ("travail", "travail", "sécurité"),
    }
    values.update(changes)
    return DocumentMetadataInput(**values)


def test_ingestion_contract_is_deterministic_and_serializable() -> None:
    item = _input()
    assert item.topics == ("sécurité", "travail")
    assert item.to_json() == item.to_json()
    assert json.loads(item.to_json())["document_kind"] == "OTHER"


@pytest.mark.parametrize(
    "unsafe_value",
    (
        r"C:\private\document.pdf",
        "/home/person/document.pdf",
        "<html><body>document</body></html>",
        "person@example.test",
        "FR7630006000011234567890189",
        "1 85 12 75 108 001 42",
        "token=super-secret-value",
        "chunk_123456",
        "x" * 501,
    ),
)
def test_ingestion_contract_rejects_sensitive_or_content_like_values(
    unsafe_value: str,
) -> None:
    with pytest.raises(ValueError):
        _input(normalized_title=unsafe_value)


def test_ingestion_contract_rejects_invalid_internal_identifier() -> None:
    with pytest.raises(ValueError, match="pseudonymous_id"):
        _input(pseudonymous_id="raw id")
