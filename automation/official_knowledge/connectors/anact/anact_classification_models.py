"""Metadata-only models for deterministic ANACT URL classification."""
from dataclasses import dataclass
from enum import StrEnum

from automation.connector_platform.connector_fingerprint import fingerprint_metadata

from .anact_models import ConfidenceLevel


class UrlCategory(StrEnum):
    THEMATIC_PAGE = "thematic_page"
    PUBLICATION = "publication"
    GUIDE = "guide"
    TOOL = "tool"
    STUDY = "study"
    DOSSIER = "dossier"
    PRACTICAL_SHEET = "practical_sheet"
    NEWS = "news"
    EVENT = "event"
    REGIONAL_ARACT_PAGE = "regional_aract_page"
    INSTITUTIONAL_PAGE = "institutional_page"
    LEGAL_PAGE = "legal_page"
    UNKNOWN_RESOURCE = "unknown_resource"


class ClassificationDecision(StrEnum):
    AUTO_ACCEPTED = "auto_accepted"
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    REJECTED = "rejected"
    UNCLASSIFIED = "unclassified"


class HumanValidationStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    RECHECK_REQUESTED = "recheck_requested"


@dataclass(frozen=True)
class ClassificationRule:
    rule_id: str
    version: str
    priority: int
    category: UrlCategory
    confidence: ConfidenceLevel
    justification: str
    exact_paths: tuple[str, ...] = ()
    path_prefixes: tuple[str, ...] = ()
    slug_tokens: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.rule_id or not self.version or self.priority < 0:
            raise ValueError("invalid classification rule")
        if not (self.exact_paths or self.path_prefixes or self.slug_tokens):
            raise ValueError("classification rule requires a matcher")

    def matches(self, path: str) -> bool:
        normalized = path.rstrip("/") or "/"
        if normalized in self.exact_paths:
            return True
        if any(normalized == prefix or normalized.startswith(prefix + "/") for prefix in self.path_prefixes):
            return True
        segments = tuple(segment for segment in normalized.lower().split("/") if segment)
        return bool(self.slug_tokens) and any(token in segment for token in self.slug_tokens for segment in segments)


@dataclass(frozen=True)
class UrlClassification:
    original_url: str
    normalized_url: str | None
    category: UrlCategory
    confidence: ConfidenceLevel
    rule_id: str
    rule_version: str
    justification: str
    region_id: str | None
    rejection_reason: str | None
    decision: ClassificationDecision
    human_validation_status: HumanValidationStatus
    fingerprint: str
    synthetic_only: bool
    fulltext: None = None

    @classmethod
    def create(
        cls,
        *,
        original_url: str,
        normalized_url: str | None,
        category: UrlCategory,
        confidence: ConfidenceLevel,
        rule_id: str,
        rule_version: str,
        justification: str,
        region_id: str | None,
        rejection_reason: str | None,
        decision: ClassificationDecision,
        human_validation_status: HumanValidationStatus,
        synthetic_only: bool,
    ) -> "UrlClassification":
        fingerprint = fingerprint_metadata((
            normalized_url or original_url,
            category.value,
            confidence.value,
            rule_id,
            rule_version,
            region_id or "",
            rejection_reason or "",
            decision.value,
        ))
        return cls(
            original_url,
            normalized_url,
            category,
            confidence,
            rule_id,
            rule_version,
            justification,
            region_id,
            rejection_reason,
            decision,
            human_validation_status,
            fingerprint,
            synthetic_only,
        )
