"""Metadata-only models for one explicitly validated ANACT page."""
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .anact_classification_models import (
    ClassificationDecision,
    HumanValidationStatus,
    UrlClassification,
)
from .anact_robots_policy import validate_candidate_url
from .anact_review_queue import ReviewItem


class PageMetadataStatus(StrEnum):
    FETCHED = "fetched"
    NOT_MODIFIED = "not_modified"
    INVALID = "invalid"
    ACCESS_DENIED = "access_denied"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"


@dataclass(frozen=True)
class PageMetadataLimits:
    timeout_seconds: float = 10
    max_redirects: int = 2
    max_response_bytes: int = 500_000
    max_title_chars: int = 500
    max_description_chars: int = 2_000
    max_json_ld_chars: int = 100_000
    max_json_ld_items: int = 20

    def __post_init__(self) -> None:
        values = (
            self.timeout_seconds,
            self.max_redirects,
            self.max_response_bytes,
            self.max_title_chars,
            self.max_description_chars,
            self.max_json_ld_chars,
            self.max_json_ld_items,
        )
        if any(value <= 0 for value in values):
            raise ValueError("invalid page metadata limits")


@dataclass(frozen=True)
class PageMetadataTarget:
    url: str
    classification_fingerprint: str
    category: str
    region_id: str | None

    @classmethod
    def from_classification(
        cls,
        classification: UrlClassification,
        *,
        human_status: HumanValidationStatus | None = None,
    ) -> "PageMetadataTarget":
        if classification.decision is ClassificationDecision.REJECTED:
            raise ValueError("rejected_classification")
        effective_human_status = human_status or classification.human_validation_status
        validated = classification.decision is ClassificationDecision.AUTO_ACCEPTED
        validated = validated or effective_human_status is HumanValidationStatus.ACCEPTED
        if not validated:
            raise ValueError("human_validation_required")
        url = classification.normalized_url
        if not url:
            raise ValueError("validated_url_required")
        policy = validate_candidate_url(url)
        if not policy.allowed:
            raise ValueError(policy.reason or "url_not_allowed")
        return cls(url, classification.fingerprint, classification.category.value, classification.region_id)

    @classmethod
    def from_review_item(cls, item: ReviewItem) -> "PageMetadataTarget":
        if item.status is not HumanValidationStatus.ACCEPTED:
            raise ValueError("human_validation_required")
        return cls.from_classification(item.classification, human_status=item.status)


@dataclass(frozen=True)
class JsonLdMetadata:
    schema_type: str | None
    name: str | None
    description: str | None
    url: str | None
    date_published: str | None
    date_modified: str | None


@dataclass(frozen=True)
class PageMetadata:
    requested_url: str
    final_url: str
    canonical_url: str | None
    title: str | None
    description: str | None
    language: str | None
    published_at: str | None
    updated_at: str | None
    content_type: str | None
    open_graph: tuple[tuple[str, str], ...]
    json_ld: tuple[JsonLdMetadata, ...]
    etag: str | None
    last_modified: str | None
    mime_type: str
    response_length: int
    classification_fingerprint: str
    category: str
    region_id: str | None
    collected_at: datetime
    fulltext: None = None

    def __post_init__(self) -> None:
        if self.fulltext is not None:
            raise ValueError("fulltext_forbidden")
        if self.response_length < 0 or self.collected_at.tzinfo is None:
            raise ValueError("invalid page metadata")


@dataclass(frozen=True)
class PageMetadataDiagnostics:
    requested_url: str
    final_url: str | None
    http_status: int | None
    mime_type: str | None
    bytes_received: int
    warnings: tuple[str, ...]
    status: PageMetadataStatus
    error_code: str | None = None


@dataclass(frozen=True)
class PageMetadataResult:
    status: PageMetadataStatus
    metadata: PageMetadata | None
    etag: str | None
    last_modified: str | None
    diagnostics: PageMetadataDiagnostics
