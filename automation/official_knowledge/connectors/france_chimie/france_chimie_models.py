"""Declarative metadata models for the inactive France Chimie connector."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from hashlib import sha256
from typing import Any, Mapping

from automation.connector_platform.connector_citation import Citation
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_license import LicenseId
from automation.connector_platform.connector_provenance import Provenance


class FranceChimieAccessStatus(StrEnum):
    NOT_ACTIVATED = "not_activated"
    PENDING_OFFICIAL_REVIEW = "pending_official_review"


class FranceChimieResourceFamily(StrEnum):
    INDUSTRY_NEWS = "industry_news"
    OCCUPATIONAL_HEALTH = "occupational_health"
    CHEMICAL_RISK = "chemical_risk"
    EMPLOYMENT_TRAINING = "employment_training"
    SOCIAL_DIALOGUE = "social_dialogue"
    REGULATION = "regulation"
    PUBLICATION = "publication"
    OTHER = "other"


class FranceChimieDocumentType(StrEnum):
    NEWS = "news"
    GUIDE = "guide"
    PRACTICAL_SHEET = "practical_sheet"
    POSITION_PAPER = "position_paper"
    STUDY = "study"
    PRESS_RELEASE = "press_release"
    PUBLICATION = "publication"
    OTHER = "other"


@dataclass(frozen=True)
class FranceChimieAccessCandidate:
    name: str
    status: FranceChimieAccessStatus

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("access candidate name is required")
        if not isinstance(self.status, FranceChimieAccessStatus):
            raise TypeError("status must be a FranceChimieAccessStatus")


@dataclass(frozen=True)
class FranceChimieDocumentIdentity:
    """Content-free identity prepared for Connector Platform interoperability."""

    reference: str | None
    title: str
    family: FranceChimieResourceFamily
    publication_date: str | None
    document_type: FranceChimieDocumentType

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title is required")
        if self.reference is not None and (not isinstance(self.reference, str) or not self.reference.strip()):
            raise ValueError("reference must be non-empty when provided")
        if not isinstance(self.family, FranceChimieResourceFamily):
            raise TypeError("family must be a FranceChimieResourceFamily")
        if not isinstance(self.document_type, FranceChimieDocumentType):
            raise TypeError("document_type must be a FranceChimieDocumentType")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["family"] = self.family.value
        value["document_type"] = self.document_type.value
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "FranceChimieDocumentIdentity":
        allowed = {"reference", "title", "family", "publication_date", "document_type"}
        if set(value) != allowed:
            raise ValueError("identity fields are incomplete or unknown")
        return cls(
            reference=value["reference"],
            title=value["title"],
            family=FranceChimieResourceFamily(value["family"]),
            publication_date=value["publication_date"],
            document_type=FranceChimieDocumentType(value["document_type"]),
        )

    def fingerprint(self) -> str:
        material = "\n".join(
            (
                self.reference or "",
                self.title,
                self.family.value,
                self.publication_date or "",
                self.document_type.value,
            )
        )
        return sha256(material.encode("utf-8")).hexdigest()

    def platform_policy(self) -> DocumentPolicy:
        return DocumentPolicy.METADATA_ONLY

    def platform_license(self) -> LicenseId:
        return LicenseId.DOCUMENT_SPECIFIC

    def citation(self, canonical_url: str) -> Citation:
        return Citation(
            canonical_url,
            self.title,
            "France Chimie",
            self.publication_date,
            self.reference,
            "official_industry_publication",
            self.platform_license().value,
            "pending_official_review",
        )

    def provenance(self, canonical_url: str) -> Provenance:
        return Provenance("france_chimie", canonical_url, None, self.fingerprint())
