"""DREETS Grand Est: Connector Platform facade, still architecture only."""
from automation.connector_platform import NETWORK_DISABLED_BY_DEFAULT

DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED="DREETS_GRAND_EST_CONNECTOR_NETWORK_NOT_IMPLEMENTED"

from .dreets_discovery import DreetsDiscoveryItem, DreetsMetadataDiscovery
from .dreets_metadata import (
    ALLOWED_DREETS_DOMAINS,
    LOT_3A_DOCUMENT_POLICY,
    DreetsDocumentPolicy,
    DreetsMetadata,
    DreetsMetadataRefusal,
)

__all__ = (
    "ALLOWED_DREETS_DOMAINS",
    "DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED",
    "DreetsDiscoveryItem",
    "DreetsDocumentPolicy",
    "DreetsMetadata",
    "DreetsMetadataDiscovery",
    "DreetsMetadataRefusal",
    "LOT_3A_DOCUMENT_POLICY",
)
