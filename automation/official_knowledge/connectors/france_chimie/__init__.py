"""Public API for the inactive France Chimie metadata-only connector."""

from .france_chimie_catalog import (
    FRANCE_CHIMIE_ACTIVE_DOMAINS,
    FRANCE_CHIMIE_DOMAIN_CANDIDATES,
    FRANCE_CHIMIE_DOMAIN_STATUS,
)
from .france_chimie_contract import (
    FRANCE_CHIMIE_DOCUMENT_CONTRACT,
    FranceChimieConnector,
    FranceChimieDocumentContract,
    FranceChimieDocumentRegistryPort,
)
from .france_chimie_metadata import (
    FRANCE_CHIMIE_CONNECTOR_NAME,
    FranceChimieMetadata,
    FranceChimieMetadataRefusal,
    metadata_from_mapping,
    normalize_injected_metadata,
)
from .france_chimie_models import (
    FranceChimieAccessCandidate,
    FranceChimieAccessStatus,
    FranceChimieDocumentIdentity,
    FranceChimieDocumentType,
    FranceChimieResourceFamily,
)
from .france_chimie_platform import (
    FRANCE_CHIMIE_NETWORK_NOT_IMPLEMENTED,
    FRANCE_CHIMIE_PLATFORM_CONTRACT,
    FRANCE_CHIMIE_REGISTRY,
    FRANCE_CHIMIE_VALIDATION,
)

__all__ = (
    "FRANCE_CHIMIE_ACTIVE_DOMAINS",
    "FRANCE_CHIMIE_CONNECTOR_NAME",
    "FRANCE_CHIMIE_DOCUMENT_CONTRACT",
    "FRANCE_CHIMIE_DOMAIN_CANDIDATES",
    "FRANCE_CHIMIE_DOMAIN_STATUS",
    "FRANCE_CHIMIE_NETWORK_NOT_IMPLEMENTED",
    "FRANCE_CHIMIE_PLATFORM_CONTRACT",
    "FRANCE_CHIMIE_REGISTRY",
    "FRANCE_CHIMIE_VALIDATION",
    "FranceChimieAccessCandidate",
    "FranceChimieAccessStatus",
    "FranceChimieConnector",
    "FranceChimieDocumentContract",
    "FranceChimieDocumentIdentity",
    "FranceChimieDocumentRegistryPort",
    "FranceChimieDocumentType",
    "FranceChimieMetadata",
    "FranceChimieMetadataRefusal",
    "FranceChimieResourceFamily",
    "metadata_from_mapping",
    "normalize_injected_metadata",
)
