from dataclasses import FrozenInstanceError

import pytest

from DOCUMENT_INTELLIGENCE_CENTER import (
    DocumentDescriptor,
    DocumentKind,
    DocumentRelation,
    RelationKind,
)


def _agreement(document_id: str = "agreement-v1") -> DocumentDescriptor:
    return DocumentDescriptor(
        document_id=document_id,
        title="Accord synthétique",
        document_kind=DocumentKind.AGREEMENT,
        provenance="catalogue-test",
        family="working-time",
        topics=(" nuit ", "temps", "nuit"),
    )


def test_descriptor_is_immutable_and_normalizes_metadata() -> None:
    document = _agreement()
    assert document.topics == ("nuit", "temps")
    with pytest.raises(FrozenInstanceError):
        document.title = "Changed"


def test_descriptor_has_no_content_or_local_path_field() -> None:
    fields = set(DocumentDescriptor.__dataclass_fields__)
    assert not fields.intersection(
        {"content", "text", "fulltext", "html", "pdf", "chunks", "local_path"}
    )


def test_relation_id_is_deterministic() -> None:
    relation = DocumentRelation(
        source_document_id="pv-1",
        target_document_id="agreement-v1",
        relation_kind=RelationKind.REFERENCES,
        provenance="explicit-metadata",
    )
    assert relation.relation_id == relation.relation_id
    assert len(relation.relation_id) == 64
