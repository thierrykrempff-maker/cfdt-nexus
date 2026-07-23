import pytest

from DOCUMENT_INTELLIGENCE_CENTER import (
    DocumentDescriptor,
    DocumentGraph,
    DocumentGraphError,
    DocumentKind,
    DocumentRelation,
    RelationKind,
)


def _document(document_id: str, kind: DocumentKind) -> DocumentDescriptor:
    return DocumentDescriptor(
        document_id=document_id,
        title=document_id,
        document_kind=kind,
        provenance="synthetic-test",
    )


def test_graph_indexes_directed_relations_and_neighbourhood() -> None:
    agreement = _document("agreement", DocumentKind.AGREEMENT)
    minutes = _document("minutes", DocumentKind.CSE_MINUTES)
    relation = DocumentRelation(
        "minutes", "agreement", RelationKind.REFERENCES, "synthetic-test"
    )
    graph = DocumentGraph((agreement, minutes), (relation,))
    assert graph.outgoing("minutes") == (relation,)
    assert graph.incoming("agreement") == (relation,)
    assert graph.related_document_ids("minutes") == ("agreement",)


def test_graph_refuses_unknown_relation_endpoint() -> None:
    graph = DocumentGraph((_document("minutes", DocumentKind.CSE_MINUTES),))
    with pytest.raises(DocumentGraphError, match="unknown documents"):
        graph.add_relation(
            DocumentRelation(
                "minutes",
                "missing",
                RelationKind.REFERENCES,
                "synthetic-test",
            )
        )


def test_graph_output_is_deterministic() -> None:
    graph = DocumentGraph(
        (
            _document("z", DocumentKind.OTHER),
            _document("a", DocumentKind.OTHER),
        )
    )
    assert tuple(item.document_id for item in graph.documents()) == ("a", "z")
