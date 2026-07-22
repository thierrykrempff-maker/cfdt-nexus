"""Public API for the generic offline Connector Adapter foundation."""

from .adapter import CONNECTOR_ADAPTATION, GenericConnectorAdapter
from .confidence import ConnectorConfidenceMapper
from .contracts import (
    ConnectorAdapter, ConnectorAdapterReporter, ConnectorAdapterValidatorProtocol,
    ConnectorSnapshotProvider,
)
from .documents import ConnectorDocumentMapper
from .evidence import ConnectorEvidenceMapper
from .metadata import ConnectorMetadataMapper
from .models import (
    ConnectorAdapterDiagnostics, ConnectorAdapterInput, ConnectorAdapterReport,
    ConnectorAdapterResult, ConnectorCapability, ConnectorDescriptor,
    ConnectorDocumentSnapshot, ConnectorQuerySnapshot, ConnectorRecordSnapshot,
    ConnectorResponseSnapshot, ConnectorResponseStatus, ConnectorSourceCategory,
    ConnectorSourceSnapshot, ConnectorValidationReport,
)
from .normalization import ConnectorSourceNormalizer
from .provenance import ConnectorProvenanceMapper
from .reporting import ConnectorAdapterReportBuilder, JsonConnectorAdapterReporter
from .validation import ConnectorAdapterValidator

__all__ = [
    "CONNECTOR_ADAPTATION", "ConnectorAdapter", "ConnectorAdapterDiagnostics",
    "ConnectorAdapterInput", "ConnectorAdapterReport", "ConnectorAdapterReportBuilder",
    "ConnectorAdapterReporter", "ConnectorAdapterResult", "ConnectorAdapterValidator",
    "ConnectorAdapterValidatorProtocol", "ConnectorCapability", "ConnectorConfidenceMapper",
    "ConnectorDescriptor", "ConnectorDocumentMapper", "ConnectorDocumentSnapshot",
    "ConnectorEvidenceMapper", "ConnectorMetadataMapper", "ConnectorProvenanceMapper",
    "ConnectorQuerySnapshot", "ConnectorRecordSnapshot", "ConnectorResponseSnapshot",
    "ConnectorResponseStatus", "ConnectorSnapshotProvider", "ConnectorSourceCategory",
    "ConnectorSourceNormalizer", "ConnectorSourceSnapshot", "ConnectorValidationReport",
    "GenericConnectorAdapter", "JsonConnectorAdapterReporter",
]
