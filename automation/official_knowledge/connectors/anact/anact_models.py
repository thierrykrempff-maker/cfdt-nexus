"""Metadata-only models for the harmonized ANACT connector foundation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from automation.connector_platform.connector_citation import Citation
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_fingerprint import fingerprint_metadata
from automation.connector_platform.connector_license import LicenseId
from automation.connector_platform.connector_provenance import Provenance
from automation.official_knowledge.document_registry import (
    DocumentRecord,
    DocumentStatus,
    stable_document_id,
)


ANACT_CONNECTOR_NAME = "anact"


class AnactResourceType(StrEnum):
    THEMATIC_PAGE = "thematic_page"
    PUBLICATION = "publication"
    GUIDE = "guide"
    TOOL = "tool"
    DOSSIER = "dossier"
    STUDY = "study"
    PRACTICAL_SHEET = "practical_sheet"
    REGIONAL_RESOURCE = "regional_resource"
    NEWS = "news"
    EVENT = "event"
    STRUCTURED_DATA = "structured_data"
    OTHER = "other"


class AnactTheme(StrEnum):
    WORKING_CONDITIONS = "working_conditions"
    QVCT = "qvct"
    OCCUPATIONAL_RISK_PREVENTION = "occupational_risk_prevention"
    WORK_ORGANIZATION = "work_organization"
    WORK_TRANSFORMATIONS = "work_transformations"
    SOCIAL_DIALOGUE = "social_dialogue"
    JOB_RETENTION = "job_retention"
    ABSENTEEISM = "absenteeism"
    OCCUPATIONAL_WEAR = "occupational_wear"
    PSYCHOSOCIAL_RISKS = "psychosocial_risks"
    PROFESSIONAL_EQUALITY = "professional_equality"
    WORKLOAD = "workload"
    REMOTE_WORK = "remote_work"
    MANAGEMENT = "management"
    OCCUPATIONAL_HEALTH = "occupational_health"
    OTHER = "other"


class GeographicScope(StrEnum):
    NATIONAL = "national"
    REGIONAL = "regional"
    UNKNOWN = "unknown"


class ValidationStatus(StrEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"


class ConfidenceLevel(StrEnum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class AccessMode(StrEnum):
    API = "api"
    OFFICIAL_FEED = "official_feed"
    HTML = "html"
    DOCUMENT = "document"
    MANUAL = "manual"


class AccessStatus(StrEnum):
    PENDING_OFFICIAL_REVIEW = "pending_official_review"


@dataclass(frozen=True)
class AnactSource:
    source_id: str
    name: str
    official_url: str | None
    scope: GeographicScope
    aract_name: str | None = None
    access_modes: tuple[AccessMode, ...] = (AccessMode.MANUAL,)
    access_status: AccessStatus = AccessStatus.PENDING_OFFICIAL_REVIEW
    synthetic_only: bool = False
    official_content: bool = False

    def __post_init__(self) -> None:
        if not self.source_id or not self.name:
            raise ValueError("source identity required")
        if self.official_url is not None and not self.official_url.startswith("https://"):
            raise ValueError("official URL must use HTTPS")
        if self.scope is GeographicScope.REGIONAL and not self.aract_name:
            raise ValueError("regional source requires ARACT name")


@dataclass(frozen=True)
class AnactResource:
    """ANACT metadata whose primary identity is its stable registry identifier.

    ``resource_id`` is retained as a secondary ANACT business reference for
    compatibility with the historical package. It is never used as the common
    document identity.
    """

    resource_id: str
    source_id: str
    resource_type: AnactResourceType
    theme: AnactTheme
    title: str
    canonical_url: str
    summary: str | None = None
    published_at: str | None = None
    updated_at: str | None = None
    collected_at: datetime | None = None
    author_or_body: str | None = None
    scope: GeographicScope = GeographicScope.UNKNOWN
    aract_name: str | None = None
    language: str = "fr"
    document_format: str | None = None
    rights: str | None = None
    validation_status: ValidationStatus = ValidationStatus.PENDING
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    synthetic_only: bool = False
    official_content: bool = False

    def __post_init__(self) -> None:
        if not self.resource_id or not self.source_id or not self.title:
            raise ValueError("resource metadata required")
        if not self.canonical_url.startswith("https://"):
            raise ValueError("canonical URL must use HTTPS")
        if self.collected_at is not None and self.collected_at.tzinfo is None:
            raise ValueError("collection date requires timezone")
        if self.scope is GeographicScope.REGIONAL and not self.aract_name:
            raise ValueError("regional resource requires ARACT name")
        if self.synthetic_only and self.official_content:
            raise ValueError("synthetic resource cannot be official content")

    @property
    def document_id(self) -> str:
        return stable_document_id(ANACT_CONNECTOR_NAME, self.canonical_url)

    def fingerprint(self) -> str:
        return fingerprint_metadata(
            (
                self.document_id,
                self.resource_id,
                self.source_id,
                self.resource_type.value,
                self.theme.value,
                self.title,
                self.canonical_url,
                self.published_at or "",
                self.updated_at or "",
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "resource_id": self.resource_id,
            "source_id": self.source_id,
            "resource_type": self.resource_type.value,
            "theme": self.theme.value,
            "title": self.title,
            "canonical_url": self.canonical_url,
            "summary": self.summary,
            "published_at": self.published_at,
            "updated_at": self.updated_at,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "author_or_body": self.author_or_body,
            "scope": self.scope.value,
            "aract_name": self.aract_name,
            "language": self.language,
            "document_format": self.document_format,
            "rights": self.rights,
            "validation_status": self.validation_status.value,
            "confidence": self.confidence.value,
            "synthetic_only": self.synthetic_only,
            "official_content": self.official_content,
            "fingerprint": self.fingerprint(),
        }

    def to_document_record(
        self,
        *,
        checked_on: str,
        first_seen: str | None = None,
        status: DocumentStatus = DocumentStatus.ACTIVE,
    ) -> DocumentRecord:
        """Build a public Document Registry record without retaining content."""

        return DocumentRecord(
            document_id=self.document_id,
            connector_name=ANACT_CONNECTOR_NAME,
            canonical_url=self.canonical_url,
            title=self.title,
            category=self.theme.value,
            family=self.scope.value,
            document_type=self.resource_type.value,
            publication_date=self.published_at,
            first_seen=first_seen or checked_on,
            last_checked=checked_on,
            last_modified_metadata=checked_on,
            language=self.language,
            provenance=ANACT_CONNECTOR_NAME,
            status=status,
        )

    def platform_policy(self) -> DocumentPolicy:
        return DocumentPolicy.METADATA_ONLY

    def platform_license(self) -> LicenseId:
        return LicenseId.DOCUMENT_SPECIFIC

    def citation(self) -> Citation:
        return Citation(
            self.canonical_url,
            self.title,
            self.author_or_body,
            self.published_at,
            self.updated_at,
            "official_prevention_guidance",
            self.platform_license().value,
            self.confidence.value,
        )

    def provenance(self) -> Provenance:
        return Provenance(ANACT_CONNECTOR_NAME, self.canonical_url, self.collected_at, self.fingerprint())
