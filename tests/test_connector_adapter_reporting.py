import json
from datetime import datetime, timezone

from NEXUS_ADAPTERS.connectors import (
    ConnectorAdapterInput, ConnectorAdapterReportBuilder, ConnectorDescriptor,
    ConnectorQuerySnapshot, ConnectorResponseSnapshot, ConnectorResponseStatus,
    ConnectorSourceCategory, ConnectorSourceSnapshot, GenericConnectorAdapter,
    JsonConnectorAdapterReporter,
)


def source():
    return ConnectorAdapterInput(
        ConnectorDescriptor("synthetic_connector", "1.0", ()),
        ConnectorSourceSnapshot("source", "SOURCE", ConnectorSourceCategory.UNKNOWN, False),
        ConnectorQuerySnapshot("query", "QUERY"),
        ConnectorResponseSnapshot(
            "response", ConnectorResponseStatus.EMPTY, source_confidence=None, duration_ms=7
        ), datetime(2026, 3, 4, tzinfo=timezone.utc),
    )


def test_json_report_is_deterministic_and_complete():
    value = source()
    result = GenericConnectorAdapter(value).adapt()
    report = ConnectorAdapterReportBuilder().build(value, result)
    reporter = JsonConnectorAdapterReporter()
    assert reporter.render(report) == reporter.render(report)
    payload = json.loads(reporter.render(report))
    assert payload["connector"] == "synthetic_connector"
    assert payload["received_documents"] == 0
    assert payload["diagnostics"]
