from datetime import datetime, timezone

from NEXUS_ADAPTERS.connectors import (
    ConnectorAdapterInput, ConnectorAdapterReportBuilder, ConnectorAdapterValidator,
    ConnectorDescriptor, ConnectorDocumentSnapshot, ConnectorQuerySnapshot,
    ConnectorResponseSnapshot, ConnectorResponseStatus, ConnectorSourceCategory,
    ConnectorSourceSnapshot, GenericConnectorAdapter, JsonConnectorAdapterReporter,
)


def source():
    document = ConnectorDocumentSnapshot(
        "doc", "source", "OTHER", "Synthetic",
        content="Bearer synthetic_token_value alice@example.test +33102030405",
    )
    return ConnectorAdapterInput(
        ConnectorDescriptor("synthetic_connector", "1.0", ()),
        ConnectorSourceSnapshot("source", "SOURCE", ConnectorSourceCategory.UNKNOWN, False),
        ConnectorQuerySnapshot("query", "QUERY"),
        ConnectorResponseSnapshot(
            "response", ConnectorResponseStatus.PARTIAL, (document,), source_confidence=None
        ), datetime(2026, 3, 4, tzinfo=timezone.utc),
    )


def test_sensitive_values_are_detected_but_never_reproduced_in_diagnostics_or_report():
    value = source()
    result = GenericConnectorAdapter(value).adapt()
    validation = ConnectorAdapterValidator().validate(value, result)
    assert any(item.code == "CONNECTOR_SENSITIVE_VALUE_DETECTED" for item in validation.diagnostics)
    report = ConnectorAdapterReportBuilder().build(value, result)
    rendered = JsonConnectorAdapterReporter().render(report)
    for forbidden in ("synthetic_token_value", "alice@example.test", "+33102030405"):
        assert forbidden not in repr(result.diagnostics)
        assert forbidden not in rendered
