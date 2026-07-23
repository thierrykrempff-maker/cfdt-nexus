import json

from DOCUMENT_INTELLIGENCE_CENTER import (
    DocumentIngestionService,
    DocumentKind,
    DocumentMetadataInput,
    IngestionAuditExporter,
    MetadataIndex,
    MetadataQuery,
    MetadataStatus,
)


def _input(document_id: str, kind: DocumentKind, date: str):
    return DocumentMetadataInput(
        pseudonymous_id=document_id,
        document_kind=kind,
        normalized_title=f"Document {document_id}",
        logical_provenance="SYNTHETIC_METADATA",
        document_date=date,
        instance="CSE",
        nature="PUBLICATION",
        status=MetadataStatus.ACTIVE,
    )


def test_metadata_index_supports_exact_fields_and_date_range() -> None:
    service = DocumentIngestionService()
    service.ingest_batch(
        (
            _input("document-00000001", DocumentKind.GUIDE, "2025-01-01"),
            _input("document-00000002", DocumentKind.STUDY, "2026-01-01"),
        )
    )
    index = MetadataIndex(service.graph.documents())
    assert tuple(
        item.document_id
        for item in index.find(
            MetadataQuery(
                date_from="2025-06-01",
                date_to="2026-12-31",
                instance="CSE",
                status="ACTIVE",
            )
        )
    ) == ("document-00000002",)


def test_audit_export_is_deterministic_and_contains_counts_only() -> None:
    service = DocumentIngestionService()
    batch = service.ingest_batch(
        (
            _input("document-00000001", DocumentKind.GUIDE, "2025-01-01"),
            _input("document-00000002", DocumentKind.STUDY, "2026-01-01"),
        )
    )
    exporter = IngestionAuditExporter()
    payload = exporter.to_json(batch, service.graph)
    assert payload == exporter.to_json(batch, service.graph)
    decoded = json.loads(payload)
    assert decoded["documents_ingested"] == 2
    assert decoded["nodes_created"] == 2
    assert decoded["statistics_by_document_type"] == {"GUIDE": 1, "STUDY": 1}
    assert "Document document-" not in payload
