from datetime import datetime, timezone

from NEXUS_ADAPTERS.connectors import (
    ConnectorAdapter, ConnectorAdapterInput, ConnectorAdapterReporter,
    ConnectorAdapterReportBuilder, ConnectorAdapterValidator,
    ConnectorAdapterValidatorProtocol, ConnectorDescriptor, ConnectorQuerySnapshot,
    ConnectorResponseSnapshot, ConnectorResponseStatus, ConnectorSnapshotProvider,
    ConnectorSourceCategory, ConnectorSourceSnapshot, GenericConnectorAdapter,
    JsonConnectorAdapterReporter,
)
from NEXUS_CORE.orchestration import ExecutableEngine


class Provider:
    def snapshot(self):
        return ConnectorResponseSnapshot("response", ConnectorResponseStatus.EMPTY)


def adapter():
    source = ConnectorAdapterInput(
        ConnectorDescriptor("synthetic_connector", "1.0", ()),
        ConnectorSourceSnapshot("source", "SOURCE", ConnectorSourceCategory.UNKNOWN, False),
        ConnectorQuerySnapshot("query", "QUERY"), Provider().snapshot(),
        datetime(2026, 3, 4, tzinfo=timezone.utc),
    )
    return GenericConnectorAdapter(source)


def test_generic_implementation_satisfies_all_protocols():
    value = adapter()
    assert isinstance(Provider(), ConnectorSnapshotProvider)
    assert isinstance(value, ConnectorAdapter)
    assert isinstance(value, ExecutableEngine)
    assert isinstance(ConnectorAdapterValidator(), ConnectorAdapterValidatorProtocol)
    assert isinstance(JsonConnectorAdapterReporter(), ConnectorAdapterReporter)


def test_public_package_has_no_network_or_connector_specific_dependency():
    import NEXUS_ADAPTERS.connectors as public_api

    namespace = " ".join(public_api.__dict__).lower()
    assert "requests" not in namespace
    assert "httpx" not in namespace
    assert "legifrance" not in namespace
