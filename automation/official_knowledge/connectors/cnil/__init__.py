"""CNIL architecture contracts backed by Connector Platform.

LOT 1 remains disabled by default and provides no production transport.
"""
from automation.connector_platform import NETWORK_DISABLED_BY_DEFAULT

CNIL_NETWORK_NOT_IMPLEMENTED = "CNIL_CONNECTOR_NETWORK_NOT_IMPLEMENTED"

from .cnil_connector import CnilConnector,build_cnil_document_registry
from .cnil_discovery import CnilDiscoveryEntry,discover_metadata
from .cnil_metadata import CnilMetadata,CnilMetadataRefusal,CnilTaxonomy
from .cnil_sync import CnilDocumentSync,CnilRedirect,CnilSyncEvent,CnilSyncEventType

__all__=(
 "CNIL_NETWORK_NOT_IMPLEMENTED","CnilConnector","CnilDiscoveryEntry","CnilMetadata",
 "CnilMetadataRefusal","CnilTaxonomy","build_cnil_document_registry","discover_metadata",
 "CnilDocumentSync","CnilRedirect","CnilSyncEvent","CnilSyncEventType",
)
