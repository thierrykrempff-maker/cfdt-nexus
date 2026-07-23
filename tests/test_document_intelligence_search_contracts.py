from DOCUMENT_INTELLIGENCE_CENTER import (
    DocumentDescriptor,
    DocumentGraph,
    DocumentKind,
    DocumentRelation,
    DocumentSearchBackend,
    RelationKind,
    SearchProjectionBuilder,
    SearchQuery,
)


def test_search_projection_contains_metadata_and_relations_only() -> None:
    agreement = DocumentDescriptor(
        "agreement",
        "Accord synthétique",
        DocumentKind.AGREEMENT,
        "synthetic-test",
        topics=("temps de travail",),
    )
    minutes = DocumentDescriptor(
        "minutes",
        "PV synthétique",
        DocumentKind.CSE_MINUTES,
        "synthetic-test",
    )
    graph = DocumentGraph(
        (agreement, minutes),
        (
            DocumentRelation(
                "minutes", "agreement", RelationKind.REFERENCES, "test"
            ),
        ),
    )
    projections = SearchProjectionBuilder().build(graph)
    assert tuple(item.document_id for item in projections) == (
        "agreement",
        "minutes",
    )
    assert projections[0].related_document_ids == ("minutes",)
    assert not hasattr(projections[0], "content")


def test_search_backend_contract_is_runtime_checkable() -> None:
    class Backend:
        def index(self, documents):
            return None

        def search(self, query):
            return ()

    assert isinstance(Backend(), DocumentSearchBackend)
    assert SearchQuery("travail de nuit", limit=5).limit == 5
