from datetime import datetime, timezone

from NEXUS_ADAPTERS.connectors import (
    ConnectorAdapterInput, ConnectorAdapterValidator, ConnectorDescriptor,
    ConnectorDocumentSnapshot, ConnectorQuerySnapshot, ConnectorResponseSnapshot,
    ConnectorResponseStatus, ConnectorSourceCategory, ConnectorSourceSnapshot,
    GenericConnectorAdapter,
)


NOW = datetime(2026, 3, 4, tzinfo=timezone.utc)


def source(document, *, score=None):
    return ConnectorAdapterInput(
        ConnectorDescriptor("synthetic_connector", "1.0", ()),
        ConnectorSourceSnapshot("source-one", "SOURCE_ONE", ConnectorSourceCategory.OTHER_OFFICIAL, True),
        ConnectorQuerySnapshot("query-one", "QUERY_ONE"),
        ConnectorResponseSnapshot(
            "response-one", ConnectorResponseStatus.PARTIAL, (document,),
            source_confidence=score,
        ), NOW,
    )


def test_incomplete_metadata_produces_diagnostics_without_exception():
    value = source(ConnectorDocumentSnapshot(None, "source-one", "OTHER"))
    result = GenericConnectorAdapter(value).adapt()
    codes = {item.code for item in result.diagnostics}
    assert {"CONNECTOR_DOCUMENT_ID_MISSING", "CONNECTOR_DOCUMENT_DATE_MISSING",
            "CONNECTOR_DOCUMENT_CONTENT_MISSING", "CONNECTOR_CONFIDENCE_MISSING"} <= codes


def test_validation_report_is_serializable_deterministic_and_non_blocking():
    value = source(ConnectorDocumentSnapshot(None, "source-one", "OTHER"))
    result = GenericConnectorAdapter(value).adapt()
    report = ConnectorAdapterValidator().validate(value, result)
    assert report.serializable is True
    assert report.deterministic is True
    assert isinstance(report.structural_violations, tuple)
