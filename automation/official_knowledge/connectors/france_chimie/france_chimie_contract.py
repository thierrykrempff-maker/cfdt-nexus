"""Document contract and inactive facade for France Chimie."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from automation.official_knowledge.document_registry import DocumentChange, DocumentRecord

from .france_chimie_catalog import FRANCE_CHIMIE_ACTIVE_DOMAINS
from .france_chimie_metadata import FranceChimieMetadata, normalize_injected_metadata
from .france_chimie_models import FranceChimieDocumentIdentity
from .france_chimie_platform import (
    FRANCE_CHIMIE_CAPABILITIES,
    FRANCE_CHIMIE_HEALTH,
    FRANCE_CHIMIE_METRICS,
    FRANCE_CHIMIE_OFFICIAL_DOMAINS,
    FRANCE_CHIMIE_PLATFORM_CONTRACT,
    FRANCE_CHIMIE_REGISTRY,
    FRANCE_CHIMIE_STATISTICS,
    FRANCE_CHIMIE_VALIDATION,
    network_not_implemented,
)


@dataclass(frozen=True)
class FranceChimieDocumentContract:
    policy: str = "METADATA_ONLY"
    cache_allowed: bool = False
    text_indexing_allowed: bool = False
    local_copy_allowed: bool = False
    pdf_storage_allowed: bool = False
    html_storage_allowed: bool = False
    full_text_allowed: bool = False
    download_allowed: bool = False
    scraping_allowed: bool = False
    provenance_required: bool = True
    citation_required: bool = True
    https_required: bool = True

    def __post_init__(self) -> None:
        if self.policy != "METADATA_ONLY":
            raise ValueError("France Chimie requires METADATA_ONLY")
        forbidden = (
            self.cache_allowed,
            self.text_indexing_allowed,
            self.local_copy_allowed,
            self.pdf_storage_allowed,
            self.html_storage_allowed,
            self.full_text_allowed,
            self.download_allowed,
            self.scraping_allowed,
        )
        if any(forbidden):
            raise ValueError("France Chimie forbids document content and transport")
        if not all((self.provenance_required, self.citation_required, self.https_required)):
            raise ValueError("provenance, citation and HTTPS are mandatory")


class FranceChimieDocumentRegistryPort(Protocol):
    def register_document(self, document: DocumentRecord) -> DocumentChange: ...
    def update_document(self, document: DocumentRecord) -> DocumentChange: ...
    def mark_removed(self, document_id: str, *, checked_on: str) -> DocumentChange: ...
    def find_document(self, document_id: str) -> DocumentRecord | None: ...
    def find_by_connector(self, connector_name: str) -> tuple[DocumentRecord, ...]: ...


FRANCE_CHIMIE_DOCUMENT_CONTRACT = FranceChimieDocumentContract()


class FranceChimieConnector:
    """Disabled facade accepting only explicitly injected local metadata."""

    platform_contract = FRANCE_CHIMIE_PLATFORM_CONTRACT
    platform_registry = FRANCE_CHIMIE_REGISTRY
    platform_validation = FRANCE_CHIMIE_VALIDATION
    capabilities = FRANCE_CHIMIE_CAPABILITIES
    health = FRANCE_CHIMIE_HEALTH
    statistics = FRANCE_CHIMIE_STATISTICS
    metrics = FRANCE_CHIMIE_METRICS
    document_contract = FRANCE_CHIMIE_DOCUMENT_CONTRACT
    official_domains = FRANCE_CHIMIE_OFFICIAL_DOMAINS
    enabled = platform_contract.enabled
    connector_status = platform_contract.state.value

    def __init__(self, *, document_registry: FranceChimieDocumentRegistryPort | None = None) -> None:
        self.document_registry = document_registry

    @property
    def document_registry_compatible(self) -> bool:
        return True

    def serialize_identity(self, identity: FranceChimieDocumentIdentity) -> dict[str, Any]:
        return identity.to_dict()

    def deserialize_identity(self, value: Mapping[str, Any]) -> FranceChimieDocumentIdentity:
        return FranceChimieDocumentIdentity.from_dict(value)

    def validate_injected_metadata(
        self,
        entries: tuple[Mapping[str, Any], ...],
        *,
        allowed_domains: frozenset[str] = FRANCE_CHIMIE_ACTIVE_DOMAINS,
        limit: int = 50,
    ) -> tuple[FranceChimieMetadata, ...]:
        return normalize_injected_metadata(entries, allowed_domains=allowed_domains, limit=limit)

    def discover(self, _scope: str):
        raise network_not_implemented()

    def fetch(self, _identity: FranceChimieDocumentIdentity):
        raise network_not_implemented()

    def synchronize(self):
        raise network_not_implemented()
