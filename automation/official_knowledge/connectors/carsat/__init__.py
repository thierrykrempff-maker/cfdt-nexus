"""CARSAT architecture-only connector; no production transport."""
from automation.connector_platform import NETWORK_DISABLED_BY_DEFAULT

CARSAT_NETWORK_NOT_IMPLEMENTED="CARSAT_CONNECTOR_NETWORK_NOT_IMPLEMENTED"

from .carsat_metadata import CarsatMetadata,CarsatMetadataRefusal
from .carsat_sync import CarsatDocumentSync,CarsatRedirect,CarsatSyncEvent,CarsatSyncEventType

__all__=("CARSAT_NETWORK_NOT_IMPLEMENTED","CarsatMetadata","CarsatMetadataRefusal","CarsatDocumentSync","CarsatRedirect","CarsatSyncEvent","CarsatSyncEventType")
