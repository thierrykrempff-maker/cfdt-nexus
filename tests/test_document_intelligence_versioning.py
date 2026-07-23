import pytest

from DOCUMENT_INTELLIGENCE_CENTER import (
    AgreementVersionManager,
    DocumentDescriptor,
    DocumentGraph,
    DocumentGraphError,
    DocumentKind,
    DocumentRelation,
    RelationKind,
)


def _version(document_id: str, date: str) -> DocumentDescriptor:
    return DocumentDescriptor(
        document_id=document_id,
        title=document_id,
        document_kind=DocumentKind.AGREEMENT,
        provenance="synthetic-test",
        effective_from=date,
        family="working-time",
    )


def test_version_manager_resolves_current_agreement() -> None:
    old = _version("v1", "2024-01-01")
    current = _version("v2", "2025-01-01")
    graph = DocumentGraph(
        (old, current),
        (
            DocumentRelation(
                "v2", "v1", RelationKind.SUPERSEDES, "catalogue-test"
            ),
        ),
    )
    report = AgreementVersionManager(graph).describe_family("working-time")
    assert report.ordered_document_ids == ("v1", "v2")
    assert report.current_document_ids == ("v2",)
    assert report.has_ambiguity is False


def test_version_manager_detects_ambiguous_unlinked_versions() -> None:
    graph = DocumentGraph((_version("v1", "2024-01-01"), _version("v2", "2025-01-01")))
    report = AgreementVersionManager(graph).describe_family("working-time")
    assert report.current_document_ids == ("v1", "v2")
    assert report.has_ambiguity is True


def test_version_manager_rejects_cycles() -> None:
    documents = (_version("v1", "2024-01-01"), _version("v2", "2025-01-01"))
    graph = DocumentGraph(
        documents,
        (
            DocumentRelation("v1", "v2", RelationKind.AMENDS, "test"),
            DocumentRelation("v2", "v1", RelationKind.AMENDS, "test"),
        ),
    )
    with pytest.raises(DocumentGraphError, match="cycle"):
        AgreementVersionManager(graph).describe_family("working-time")
