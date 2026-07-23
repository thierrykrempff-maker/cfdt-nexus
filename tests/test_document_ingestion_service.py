from DOCUMENT_INTELLIGENCE_CENTER import (
    AgreementMetadataInput,
    AgreementNature,
    DocumentIngestionService,
    DocumentKind,
    DocumentMetadataInput,
    ExplicitDocumentLink,
    IngestionDecision,
    MetadataStatus,
    RelationKind,
)


def _document(document_id: str, **changes) -> DocumentMetadataInput:
    values = {
        "pseudonymous_id": document_id,
        "document_kind": DocumentKind.OTHER,
        "normalized_title": f"Document {document_id}",
        "logical_provenance": "SYNTHETIC_METADATA",
        "document_date": "2026-01-01",
        "instance": "CSE",
        "nature": "NOTE",
        "status": MetadataStatus.ACTIVE,
    }
    values.update(changes)
    return DocumentMetadataInput(**values)


def _agreement(
    document_id: str,
    version: str,
    *,
    date: str,
    status: MetadataStatus = MetadataStatus.ACTIVE,
    link: ExplicitDocumentLink | None = None,
) -> AgreementMetadataInput:
    return AgreementMetadataInput(
        pseudonymous_id=document_id,
        normalized_title=f"Accord {version}",
        logical_provenance="SYNTHETIC_AGREEMENT_METADATA",
        nature=AgreementNature.AGREEMENT,
        family="working-time",
        agreement_reference="ACC-TT",
        version=version,
        signature_date=date,
        effective_from=date,
        status=status,
        parent_link=link,
    )


def test_single_and_batch_ingestion_create_nodes() -> None:
    service = DocumentIngestionService()
    first = service.ingest(_document("document-00000001"))
    batch = service.ingest_batch(
        (
            _document("document-00000002", document_date="2026-02-01"),
            _document("document-00000003", document_date="2026-03-01"),
        )
    )
    assert first.decision is IngestionDecision.CREATED
    assert batch.created == 2
    assert len(service.graph.documents()) == 3


def test_reingestion_is_idempotent() -> None:
    service = DocumentIngestionService()
    item = _document("document-00000001")
    assert service.ingest(item).decision is IngestionDecision.CREATED
    assert service.ingest(item).decision is IngestionDecision.DUPLICATE
    assert len(service.graph.documents()) == 1


def test_controlled_metadata_key_detects_duplicate_identity() -> None:
    service = DocumentIngestionService()
    first = _document("document-00000001")
    duplicate = _document("document-00000002")
    service.ingest(first)
    result = service.ingest(duplicate)
    assert result.decision is IngestionDecision.DUPLICATE
    assert result.issues[0].code == "DUPLICATE_METADATA"
    assert len(service.graph.documents()) == 1


def test_existing_node_metadata_can_be_updated() -> None:
    service = DocumentIngestionService()
    service.ingest(_document("document-00000001"))
    result = service.ingest(
        _document(
            "document-00000001",
            normalized_title="Titre normalisé corrigé",
        )
    )
    assert result.decision is IngestionDecision.UPDATED
    assert (
        service.graph.find_document("document-00000001").title
        == "Titre normalisé corrigé"
    )


def test_same_identity_with_different_type_is_rejected() -> None:
    service = DocumentIngestionService()
    service.ingest(_document("document-00000001"))
    result = service.ingest(
        _document(
            "document-00000001",
            document_kind=DocumentKind.GUIDE,
        )
    )
    assert result.decision is IngestionDecision.REJECTED
    assert result.issues[0].code == "DOCUMENT_TYPE_CONFLICT"


def test_agreement_version_date_conflict_is_explicit() -> None:
    service = DocumentIngestionService()
    service.ingest(_agreement("agreement-00000001", "1", date="2025-01-01"))
    result = service.ingest(
        _agreement("agreement-00000002", "1", date="2025-02-01")
    )
    assert result.decision is IngestionDecision.REJECTED
    assert result.issues[0].code == "AGREEMENT_VERSION_DATE_CONFLICT"


def test_agreement_status_conflict_is_explicit() -> None:
    service = DocumentIngestionService()
    service.ingest(_agreement("agreement-00000001", "1", date="2025-01-01"))
    result = service.ingest(
        _agreement(
            "agreement-00000002",
            "1",
            date="2025-01-01",
            status=MetadataStatus.REPLACED,
        )
    )
    assert result.decision is IngestionDecision.REJECTED
    assert result.issues[0].code == "AGREEMENT_STATUS_CONFLICT"


def test_source_quality_warning_is_reported_without_copying_its_value() -> None:
    service = DocumentIngestionService()
    item = _document(
        "document-00000001",
        quality_warnings=("date à confirmer",),
    )
    result = service.ingest(item)
    assert result.issues[0].code == "SOURCE_METADATA_WARNING"
    assert "date à confirmer" not in result.issues[0].description


def test_batch_creates_explicit_pv_agreement_relation() -> None:
    service = DocumentIngestionService()
    agreement = _agreement("agreement-00000001", "1", date="2025-01-01")
    minutes = _document(
        "minutes-00000001",
        document_kind=DocumentKind.CSE_MINUTES,
        explicit_links=(
            ExplicitDocumentLink(
                "agreement-00000001",
                RelationKind.REFERENCES,
            ),
        ),
    )
    batch = service.ingest_batch((minutes, agreement))
    assert batch.created == 2
    assert batch.relation_count == 1
    assert service.graph.relations()[0].relation_kind is RelationKind.REFERENCES


def test_missing_relation_target_is_reported_without_silent_failure() -> None:
    service = DocumentIngestionService()
    result = service.ingest(
        _document(
            "minutes-00000001",
            explicit_links=(
                ExplicitDocumentLink(
                    "agreement-99999999",
                    RelationKind.REFERENCES,
                ),
            ),
        )
    )
    assert result.issues[0].code == "RELATION_TARGET_MISSING"
    assert service.graph.find_document("minutes-00000001") is not None


def test_agreement_version_cycle_is_rejected() -> None:
    service = DocumentIngestionService()
    first = _agreement(
        "agreement-00000001",
        "1",
        date="2025-01-01",
        link=ExplicitDocumentLink(
            "agreement-00000002",
            RelationKind.SUPERSEDES,
        ),
    )
    second = _agreement(
        "agreement-00000002",
        "2",
        date="2026-01-01",
        link=ExplicitDocumentLink(
            "agreement-00000001",
            RelationKind.SUPERSEDES,
        ),
    )
    result = service.ingest_batch((first, second))
    assert result.relation_count == 1
    assert any(
        issue.code == "AGREEMENT_VERSION_CYCLE" for issue in result.issues
    )
