from DOCUMENT_INTELLIGENCE_CENTER import (
    DocumentDescriptor,
    DocumentGraph,
    DocumentKind,
    DocumentNavigationService,
    DocumentRelation,
    NavigationDirection,
    NavigationQuery,
    RelationKind,
)


def _document(
    document_id: str,
    kind: DocumentKind,
    *,
    date: str,
    family: str | None = None,
    instance: str | None = None,
    status: str = "ACTIVE",
    version: str | None = None,
) -> DocumentDescriptor:
    return DocumentDescriptor(
        document_id=document_id,
        title=f"Document {document_id}",
        document_kind=kind,
        provenance="SYNTHETIC_METADATA",
        publication_date=date,
        effective_from=date,
        family=family,
        instance=instance,
        status=status,
        version_label=version,
    )


def _service() -> DocumentNavigationService:
    documents = (
        _document(
            "agreement-00000001",
            DocumentKind.AGREEMENT,
            date="2024-01-01",
            family="working-time",
            version="1",
        ),
        _document(
            "agreement-00000002",
            DocumentKind.AGREEMENT,
            date="2025-01-01",
            family="working-time",
            version="2",
        ),
        _document(
            "minutes-00000001",
            DocumentKind.CSE_MINUTES,
            date="2025-02-01",
            instance="CSE",
        ),
        _document(
            "guide-00000000001",
            DocumentKind.GUIDE,
            date="2025-03-01",
        ),
        _document(
            "orphan-000000001",
            DocumentKind.STUDY,
            date="2026-01-01",
        ),
    )
    relations = (
        DocumentRelation(
            "agreement-00000002",
            "agreement-00000001",
            RelationKind.SUPERSEDES,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-00000001",
            "agreement-00000002",
            RelationKind.REFERENCES,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "guide-00000000001",
            "minutes-00000001",
            RelationKind.RELATED_TO,
            "SYNTHETIC_METADATA",
        ),
    )
    return DocumentNavigationService(DocumentGraph(documents, relations))


def test_get_document_returns_safe_projection() -> None:
    document = _service().get_document("minutes-00000001")
    assert document.document_kind is DocumentKind.CSE_MINUTES
    assert document.instance == "CSE"
    assert not hasattr(document, "canonical_url")
    assert not hasattr(document, "content")


def test_navigation_supports_incoming_and_outgoing_relations() -> None:
    service = _service()
    incoming = service.incoming("agreement-00000002")
    outgoing = service.outgoing("agreement-00000002")
    assert {item.document_id for item in incoming.documents} == {
        "agreement-00000002",
        "minutes-00000001",
    }
    assert {item.document_id for item in outgoing.documents} == {
        "agreement-00000001",
        "agreement-00000002",
    }


def test_multi_relation_navigation_is_depth_limited() -> None:
    result = _service().related_documents(
        "agreement-00000001",
        max_depth=3,
    )
    assert {item.document_id for item in result.documents} == {
        "agreement-00000001",
        "agreement-00000002",
        "minutes-00000001",
        "guide-00000000001",
    }
    assert len(result.relations) == 3


def test_navigation_query_is_deterministic() -> None:
    query = NavigationQuery(
        document_id="agreement-00000002",
        relation_kinds=(
            RelationKind.SUPERSEDES,
            RelationKind.REFERENCES,
            RelationKind.SUPERSEDES,
        ),
        direction=NavigationDirection.BOTH,
    )
    assert query.relation_kinds == (
        RelationKind.REFERENCES,
        RelationKind.SUPERSEDES,
    )
    assert _service().search(query).to_json() == _service().search(
        query
    ).to_json()
