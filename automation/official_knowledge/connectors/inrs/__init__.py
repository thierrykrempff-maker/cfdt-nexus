"""Official INRS metadata discovery and synchronization; no production transport."""
from automation.connector_platform import NETWORK_DISABLED_BY_DEFAULT

INRS_NETWORK_NOT_IMPLEMENTED="INRS_CONNECTOR_NETWORK_NOT_IMPLEMENTED"

from .inrs_connector import InrsConnector
from .inrs_contract import INRS_DOCUMENT_CONTRACT,InrsDocumentRegistryPort
from .inrs_metadata import InrsMetadata,InrsMetadataDocumentType,InrsMetadataFamily,InrsMetadataRefusal
from .inrs_sync import InrsDocumentSync,InrsRedirect,InrsSyncEvent,InrsSyncEventType

__all__=("INRS_NETWORK_NOT_IMPLEMENTED","INRS_DOCUMENT_CONTRACT","InrsConnector","InrsDocumentRegistryPort","InrsMetadata","InrsMetadataDocumentType","InrsMetadataFamily","InrsMetadataRefusal","InrsDocumentSync","InrsRedirect","InrsSyncEvent","InrsSyncEventType")
