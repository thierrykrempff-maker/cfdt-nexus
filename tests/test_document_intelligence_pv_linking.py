from DOCUMENT_INTELLIGENCE_CENTER import (
    DocumentDescriptor,
    DocumentKind,
    PVAgreementLinker,
    RelationKind,
)


def _agreement(document_id: str, url: str) -> DocumentDescriptor:
    return DocumentDescriptor(
        document_id=document_id,
        title=document_id,
        document_kind=DocumentKind.AGREEMENT,
        provenance="synthetic-test",
        canonical_url=url,
    )


def test_linker_uses_explicit_ids_and_urls_only() -> None:
    agreements = (
        _agreement("agreement-a", "https://example.test/agreements/a"),
        _agreement("agreement-b", "https://example.test/agreements/b"),
    )
    minutes = DocumentDescriptor(
        document_id="pv-1",
        title="PV synthétique",
        document_kind=DocumentKind.CSE_MINUTES,
        provenance="synthetic-test",
        referenced_document_ids=("agreement-a",),
        referenced_canonical_urls=("https://example.test/agreements/b",),
    )
    relations = PVAgreementLinker().link(minutes, agreements)
    assert tuple(item.target_document_id for item in relations) == (
        "agreement-a",
        "agreement-b",
    )
    assert {item.relation_kind for item in relations} == {RelationKind.REFERENCES}


def test_linker_does_not_infer_from_similar_titles() -> None:
    agreement = _agreement("agreement-a", "https://example.test/agreements/a")
    minutes = DocumentDescriptor(
        document_id="pv-1",
        title="Discussion de agreement-a",
        document_kind=DocumentKind.CSE_MINUTES,
        provenance="synthetic-test",
    )
    assert PVAgreementLinker().link(minutes, (agreement,)) == ()
