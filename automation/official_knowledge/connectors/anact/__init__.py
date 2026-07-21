"""Stable public API for the inactive metadata-only ANACT foundation.

Network transports deliberately remain available only through their explicit
modules and are never imported as a side effect of importing this package.
"""

from .anact_catalog import ANACT_NATIONAL_SOURCE, SOURCE_FAMILIES, SOURCES, get_source
from .anact_contract import (
    ANACT_DOCUMENT_CONTRACT,
    AnactConnector,
    AnactConnectorContract,
    AnactDocumentContract,
    AnactDocumentRegistryPort,
    ResourceValidation,
)
from .anact_models import (
    ANACT_CONNECTOR_NAME,
    AccessMode,
    AccessStatus,
    AnactResource,
    AnactResourceType,
    AnactSource,
    AnactTheme,
    ConfidenceLevel,
    GeographicScope,
    ValidationStatus,
)
from .anact_platform import (
    ANACT_NETWORK_NOT_IMPLEMENTED,
    ANACT_PLATFORM_CONTRACT,
    ANACT_REGISTRY,
    ANACT_VALIDATION,
)

__all__ = (
    "ANACT_CONNECTOR_NAME",
    "ANACT_DOCUMENT_CONTRACT",
    "ANACT_NATIONAL_SOURCE",
    "ANACT_NETWORK_NOT_IMPLEMENTED",
    "ANACT_PLATFORM_CONTRACT",
    "ANACT_REGISTRY",
    "ANACT_VALIDATION",
    "SOURCE_FAMILIES",
    "SOURCES",
    "AccessMode",
    "AccessStatus",
    "AnactConnector",
    "AnactConnectorContract",
    "AnactDocumentContract",
    "AnactDocumentRegistryPort",
    "AnactResource",
    "AnactResourceType",
    "AnactSource",
    "AnactTheme",
    "ConfidenceLevel",
    "GeographicScope",
    "ResourceValidation",
    "ValidationStatus",
    "get_source",
)
