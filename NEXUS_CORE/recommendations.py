"""Non-legal recommendations for data collection and human review."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .identifiers import EvidenceId, FindingId, RecommendationId
from .privacy import MetadataEntry


class RecommendationType(str, Enum):
    REQUEST_DOCUMENT = "request_document"
    VERIFY_INFORMATION = "verify_information"
    MANUAL_REVIEW = "manual_review"
    CONSULT_EXPERT = "consult_expert"
    CORRECT_DATA = "correct_data"
    INVESTIGATE = "investigate"
    NO_ACTION = "no_action"


class RecommendationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class RecommendationStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    DISMISSED = "dismissed"


@dataclass(frozen=True, slots=True)
class Recommendation:
    recommendation_id: RecommendationId
    recommendation_type: RecommendationType
    priority: RecommendationPriority
    status: RecommendationStatus
    code: str
    evidence_references: tuple[EvidenceId, ...] = ()
    finding_references: tuple[FindingId, ...] = ()
    metadata: tuple[MetadataEntry, ...] = ()
    schema_version: str = "1.0"
