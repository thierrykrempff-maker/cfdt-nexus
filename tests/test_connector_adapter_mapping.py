from datetime import date, datetime, timezone

from NEXUS_ADAPTERS.connectors import (
    ConnectorAdapterInput, ConnectorCapability, ConnectorDescriptor,
    ConnectorDocumentSnapshot, ConnectorQuerySnapshot, ConnectorRecordSnapshot,
    ConnectorResponseSnapshot, ConnectorResponseStatus, ConnectorSourceCategory,
    ConnectorSourceSnapshot, GenericConnectorAdapter,
)
from NEXUS_CORE import DocumentType


NOW = datetime(2026, 3, 4, tzinfo=timezone.utc)


def source(documents, records=(), category=ConnectorSourceCategory.LEGISLATION):
    return ConnectorAdapterInput(
        ConnectorDescriptor("synthetic_connector", "1.0", (ConnectorCapability.DOCUMENTS,)),
        ConnectorSourceSnapshot("source-one", "SOURCE_ONE", category, True),
        ConnectorQuerySnapshot("query-one", "QUERY_ONE"),
        ConnectorResponseSnapshot(
            "response-one", ConnectorResponseStatus.SUCCEEDED,
            documents, records, source_confidence=0.75,
        ), NOW,
    )


def document(identifier):
    return ConnectorDocumentSnapshot(
        identifier, "source-one", "LEGISLATION", f"Synthetic {identifier}",
        publication_date=date(2026, 1, 1), content="synthetic content",
    )


def test_maps_one_and_multiple_official_documents():
    one = GenericConnectorAdapter(source((document("one"),))).adapt()
    many = GenericConnectorAdapter(source((document("one"), document("two")))).adapt()
    assert one.documents[0].document_type is DocumentType.LEGAL_TEXT
    assert len(many.documents) == len(many.evidence) == 2
    assert many.documents[0].source.reference == many.provenances[0].source


def test_unknown_source_is_preserved_with_non_blocking_diagnostic():
    result = GenericConnectorAdapter(source(
        (document("one"),), category=ConnectorSourceCategory.UNKNOWN
    )).adapt()
    assert result.documents
    assert any(item.code == "CONNECTOR_SOURCE_UNKNOWN" for item in result.diagnostics)


def test_finding_requires_an_explicit_source_conclusion():
    records = (
        ConnectorRecordSnapshot("record-one", "search_hit"),
        ConnectorRecordSnapshot(
            "record-two", "source_conclusion", explicit_conclusion_code="SOURCE_RESULT",
            explicit_conclusion="synthetic conclusion",
        ),
    )
    result = GenericConnectorAdapter(source((), records)).adapt()
    assert len(result.findings) == 1
    assert result.findings[0].code == "CONNECTOR_EXPLICIT_CONCLUSION"
