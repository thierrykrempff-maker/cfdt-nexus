"""Internal metadata-only models for the ANACT document catalogue."""
from dataclasses import dataclass, replace
from enum import StrEnum

from automation.connector_platform.connector_deduplication import deduplicate
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_fingerprint import fingerprint_metadata
from automation.connector_platform.connector_license import LicenseId
from automation.connector_platform.connector_versioning import DocumentVersion

from .anact_catalog import CONFIRMED_ENTRY_POINTS
from .anact_classification_models import (
    ClassificationDecision,
    HumanValidationStatus,
    UrlClassification,
)
from .anact_page_metadata_models import PageMetadata


class CatalogLifecycle(StrEnum):
    ACTIVE = "active"
    DISAPPEARED = "disappeared"


class CatalogChange(StrEnum):
    NEW = "new"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"
    DISAPPEARED = "disappeared"


@dataclass(frozen=True)
class CatalogDocument:
    document_id: str
    url: str
    canonical_url: str
    aliases: tuple[str, ...]
    category: str
    region_id: str | None
    language: str | None
    title: str | None
    description: str | None
    published_at: str | None
    updated_at: str | None
    mime_type: str
    etag: str | None
    last_modified: str | None
    confidence: str
    validation_decision: str
    human_validation_status: str
    discovery_source: str
    classifier_version: str
    document_policy: str
    license_id: str
    metadata_fingerprint: str
    lifecycle: CatalogLifecycle = CatalogLifecycle.ACTIVE

    @classmethod
    def from_metadata(
        cls,
        metadata: PageMetadata,
        classification: UrlClassification,
        *,
        human_status: HumanValidationStatus | None = None,
    ) -> "CatalogDocument":
        if metadata.fulltext is not None:
            raise ValueError("fulltext_forbidden")
        if metadata.classification_fingerprint != classification.fingerprint:
            raise ValueError("classification_fingerprint_mismatch")
        if metadata.category != classification.category.value or metadata.region_id != classification.region_id:
            raise ValueError("classification_metadata_mismatch")
        if classification.decision is ClassificationDecision.REJECTED:
            raise ValueError("rejected_resource")
        effective_human_status = human_status or classification.human_validation_status
        validated = classification.decision is ClassificationDecision.AUTO_ACCEPTED
        validated = validated or effective_human_status is HumanValidationStatus.ACCEPTED
        if not validated:
            raise ValueError("human_validation_required")

        canonical = metadata.canonical_url or metadata.final_url
        aliases = tuple(sorted(deduplicate([
            metadata.requested_url,
            metadata.final_url,
            canonical,
        ]).unique_fingerprints))
        document_id = fingerprint_metadata(("anact", canonical))
        values = (
            canonical,
            "|".join(aliases),
            classification.category.value,
            classification.region_id or "",
            metadata.language or "",
            metadata.title or "",
            metadata.description or "",
            metadata.published_at or "",
            metadata.updated_at or "",
            metadata.mime_type,
            metadata.etag or "",
            metadata.last_modified or "",
            classification.confidence.value,
            classification.decision.value,
            effective_human_status.value,
            classification.rule_version,
        )
        return cls(
            document_id,
            metadata.requested_url,
            canonical,
            aliases,
            classification.category.value,
            classification.region_id,
            metadata.language,
            metadata.title,
            metadata.description,
            metadata.published_at,
            metadata.updated_at,
            metadata.mime_type,
            metadata.etag,
            metadata.last_modified,
            classification.confidence.value,
            classification.decision.value,
            effective_human_status.value,
            CONFIRMED_ENTRY_POINTS["sitemap"],
            classification.rule_version,
            DocumentPolicy.METADATA_ONLY.value,
            LicenseId.DOCUMENT_SPECIFIC.value,
            fingerprint_metadata(values),
        )

    def with_identity(self, document_id: str, aliases: tuple[str, ...]) -> "CatalogDocument":
        return replace(self, document_id=document_id, aliases=aliases, lifecycle=CatalogLifecycle.ACTIVE)

    def with_lifecycle(self, lifecycle: CatalogLifecycle) -> "CatalogDocument":
        return replace(self, lifecycle=lifecycle)

    def version_fingerprint(self) -> str:
        return fingerprint_metadata((self.metadata_fingerprint, self.lifecycle.value))


@dataclass(frozen=True)
class CatalogVersionEvent:
    change: CatalogChange
    document: CatalogDocument
    version: DocumentVersion | None


@dataclass(frozen=True)
class CatalogQuery:
    category: str | None = None
    region_id: str | None = None
    language: str | None = None
    lifecycle: CatalogLifecycle | None = None
    validation_decision: str | None = None
    human_validation_status: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    title_term: str | None = None
    description_term: str | None = None


@dataclass(frozen=True)
class CatalogExport:
    schema_version: str
    records: tuple[CatalogDocument, ...]
    versions: tuple[DocumentVersion, ...]
