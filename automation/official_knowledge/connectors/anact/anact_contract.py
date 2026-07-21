"""Offline ANACT connector facade and metadata-only document contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from automation.connector_platform.connector_health import HealthReport
from automation.connector_platform.connector_provenance import Provenance
from automation.official_knowledge.document_registry import DocumentChange, DocumentRecord

from .anact_catalog import SOURCES, get_source
from .anact_classification_models import UrlClassification
from .anact_freshness import FRESHNESS_POLICIES, FreshnessPolicy
from .anact_legal_policy import ANACT_LEGAL_POLICY, LegalPolicy
from .anact_models import AnactResource, AnactSource
from .anact_platform import (
    ANACT_CAPABILITIES,
    ANACT_HEALTH,
    ANACT_METRICS,
    ANACT_PLATFORM_CONTRACT,
    ANACT_REGISTRY,
    ANACT_STATISTICS,
    ANACT_VALIDATION,
    operation_not_implemented,
)
from .anact_review_queue import AnactReviewQueue
from .anact_source_audit import AUDIT_RECORDS, SourceAuditRecord
from .anact_url_classifier import AnactUrlClassifier

if TYPE_CHECKING:
    from .anact_page_metadata_models import PageMetadataResult, PageMetadataTarget
    from .anact_page_metadata_transport import AnactPageMetadataTransport
    from .anact_sitemap_transport import AnactSitemapTransport
    from .anact_transport_models import ConditionalState, SitemapCandidate, SitemapInspectionResult


@dataclass(frozen=True)
class ResourceValidation:
    valid: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnactDocumentContract:
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
            raise ValueError("ANACT requires METADATA_ONLY")
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
            raise ValueError("ANACT foundation forbids content and transport")
        if not all((self.provenance_required, self.citation_required, self.https_required)):
            raise ValueError("provenance, citation and HTTPS are mandatory")


class AnactDocumentRegistryPort(Protocol):
    def register_document(self, document: DocumentRecord) -> DocumentChange: ...
    def update_document(self, document: DocumentRecord) -> DocumentChange: ...
    def mark_removed(self, document_id: str, *, checked_on: str) -> DocumentChange: ...
    def find_document(self, document_id: str) -> DocumentRecord | None: ...
    def find_by_connector(self, connector_name: str) -> tuple[DocumentRecord, ...]: ...


class AnactConnectorContract(Protocol):
    def list_sources(self) -> tuple[AnactSource, ...]: ...
    def discover(self, source_id: str) -> list[AnactResource]: ...
    def fetch(self, document_id: str) -> bytes: ...
    def normalize(self, resource: AnactResource) -> AnactResource: ...
    def validate_resource(self, resource: AnactResource) -> ResourceValidation: ...
    def trace(self, resource: AnactResource) -> Provenance: ...
    def diagnose(self) -> HealthReport: ...
    def synchronize(self) -> None: ...


ANACT_DOCUMENT_CONTRACT = AnactDocumentContract()


class AnactConnector:
    connector_id = "anact"
    platform_contract = ANACT_PLATFORM_CONTRACT
    platform_registry = ANACT_REGISTRY
    platform_validation = ANACT_VALIDATION
    capabilities = ANACT_CAPABILITIES
    health = ANACT_HEALTH
    statistics = ANACT_STATISTICS
    metrics = ANACT_METRICS
    document_contract = ANACT_DOCUMENT_CONTRACT
    enabled = platform_contract.enabled
    connector_status = platform_contract.state.value
    sitemap_transport_implemented = True
    sitemap_transport_enabled_by_default = False
    page_metadata_transport_implemented = True
    page_metadata_transport_enabled_by_default = False

    def __init__(self, *, document_registry: AnactDocumentRegistryPort | None = None) -> None:
        self.document_registry = document_registry

    @property
    def document_registry_compatible(self) -> bool:
        return True

    def list_sources(self) -> tuple[AnactSource, ...]:
        return SOURCES

    def source_audit(self) -> tuple[SourceAuditRecord, ...]:
        return AUDIT_RECORDS

    def legal_policy(self) -> LegalPolicy:
        return ANACT_LEGAL_POLICY

    def freshness_policies(self) -> tuple[FreshnessPolicy, ...]:
        return FRESHNESS_POLICIES

    def inspect_sitemap(self, transport: AnactSitemapTransport, state: ConditionalState | None = None) -> SitemapInspectionResult:
        if state is None:
            from .anact_transport_models import ConditionalState

            state = ConditionalState()
        return transport.inspect(state)

    def classify_candidate(self, candidate: SitemapCandidate) -> UrlClassification:
        return AnactUrlClassifier().classify_candidate(candidate)

    def classify_candidates(self, candidates: tuple[SitemapCandidate, ...]) -> tuple[UrlClassification, ...]:
        return AnactUrlClassifier().classify_candidates(candidates)

    def new_review_queue(self) -> AnactReviewQueue:
        return AnactReviewQueue()

    def read_page_metadata(
        self,
        target: PageMetadataTarget,
        transport: AnactPageMetadataTransport,
        state: ConditionalState | None = None,
    ) -> PageMetadataResult:
        if state is None:
            from .anact_transport_models import ConditionalState

            state = ConditionalState()
        return transport.inspect(target, state)

    def normalize(self, resource: AnactResource) -> AnactResource:
        return resource

    def to_document_record(
        self,
        resource: AnactResource,
        *,
        checked_on: str,
        first_seen: str | None = None,
    ) -> DocumentRecord:
        return resource.to_document_record(checked_on=checked_on, first_seen=first_seen)

    def validate_resource(self, resource: AnactResource) -> ResourceValidation:
        errors: list[str] = []
        try:
            get_source(resource.source_id)
        except KeyError:
            errors.append("unknown_source")
        if not resource.synthetic_only:
            errors.append("architecture_only_requires_synthetic_resource")
        if resource.official_content:
            errors.append("official_content_forbidden")
        return ResourceValidation(not errors, tuple(errors))

    def trace(self, resource: AnactResource) -> Provenance:
        return resource.provenance()

    def diagnose(self) -> HealthReport:
        return self.health

    def discover(self, _source_id: str):
        raise operation_not_implemented()

    def fetch(self, _document_id: str):
        raise operation_not_implemented()

    def synchronize(self):
        raise operation_not_implemented()
