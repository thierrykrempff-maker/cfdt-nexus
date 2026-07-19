"""INRS LOT 0 architecture only; no production transport."""
from automation.connector_platform import NETWORK_DISABLED_BY_DEFAULT

INRS_NETWORK_NOT_IMPLEMENTED="INRS_CONNECTOR_NETWORK_NOT_IMPLEMENTED"

from .inrs_connector import InrsConnector
from .inrs_contract import INRS_DOCUMENT_CONTRACT,InrsDocumentRegistryPort

__all__=("INRS_NETWORK_NOT_IMPLEMENTED","INRS_DOCUMENT_CONTRACT","InrsConnector","InrsDocumentRegistryPort")
