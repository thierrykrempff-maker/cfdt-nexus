"""Immutable contracts for traceable searches in CSE and CSSCT minutes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from .retrieval_models import redact_public_value


NOT_A_LEGAL_NORM = "Ce passage n’est pas présenté comme une norme juridique."


class MeetingBody(str, Enum):
    CSE = "CSE"
    CSSCT = "CSSCT"
    CE = "CE"
    CHSCT = "CHSCT"
    COMMISSION = "COMMISSION"
    JOINT_MEETING = "JOINT_MEETING"
    UNKNOWN = "UNKNOWN"


class MeetingType(str, Enum):
    ORDINARY = "ORDINARY"
    EXTRAORDINARY = "EXTRAORDINARY"
    SPECIAL = "SPECIAL"
    PREPARATORY = "PREPARATORY"
    FOLLOW_UP = "FOLLOW_UP"
    UNKNOWN = "UNKNOWN"


class PassageNature(str, Enum):
    EMPLOYEE_REPRESENTATIVE_QUESTION = "EMPLOYEE_REPRESENTATIVE_QUESTION"
    MANAGEMENT_RESPONSE = "MANAGEMENT_RESPONSE"
    MANAGEMENT_INFORMATION = "MANAGEMENT_INFORMATION"
    OBSERVATION = "OBSERVATION"
    FINDING = "FINDING"
    COMMITMENT = "COMMITMENT"
    DECISION = "DECISION"
    REQUEST = "REQUEST"
    WARNING = "WARNING"
    DISAGREEMENT = "DISAGREEMENT"
    FOLLOW_UP = "FOLLOW_UP"
    DISCUSSION = "DISCUSSION"
    DOCUMENT_REFERENCE = "DOCUMENT_REFERENCE"
    UNKNOWN = "UNKNOWN"


class SpeakerRole(str, Enum):
    MANAGEMENT = "MANAGEMENT"
    ELECTED_REPRESENTATIVE = "ELECTED_REPRESENTATIVE"
    UNION_REPRESENTATIVE = "UNION_REPRESENTATIVE"
    CSSCT_MEMBER = "CSSCT_MEMBER"
    EXPERT = "EXPERT"
    OCCUPATIONAL_HEALTH = "OCCUPATIONAL_HEALTH"
    SAFETY_DEPARTMENT = "SAFETY_DEPARTMENT"
    EMPLOYEE = "EMPLOYEE"
    UNKNOWN = "UNKNOWN"


class SearchMode(str, Enum):
    LEXICAL_ONLY = "LEXICAL_ONLY"
    HYBRID_LOCAL = "HYBRID_LOCAL"
    HYBRID_EMBEDDING = "HYBRID_EMBEDDING"
    DEGRADED_MODE = "DEGRADED_MODE"


@dataclass(frozen=True, slots=True)
class PVDocument:
    document_id: str
    title: str
    public_title: str
    meeting_body: MeetingBody
    meeting_type: MeetingType
    meeting_date: str | None
    meeting_date_confidence: str
    establishment: str | None
    source_path_hash: str
    original_file_type: str
    page_count: int | None
    chunk_count: int
    indexed_at: str
    version: str
    confidential: bool
    metadata_warnings: tuple[str, ...] = ()
    document_kind: str = "minutes"

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.document_id,
                self.title,
                self.public_title,
                self.meeting_date_confidence,
                self.source_path_hash,
                self.original_file_type,
                self.indexed_at,
                self.version,
            )
        ):
            raise ValueError("PV document identity and provenance are required")
        if self.chunk_count < 0 or (self.page_count is not None and self.page_count < 0):
            raise ValueError("PV document counters cannot be negative")

    def to_dict(self, *, public: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        payload["meeting_body"] = self.meeting_body.value
        payload["meeting_type"] = self.meeting_type.value
        if public:
            payload.pop("source_path_hash", None)
            payload.pop("title", None)
            payload.pop("confidential", None)
        return payload


@dataclass(frozen=True, slots=True)
class PVPassage:
    passage_id: str
    document_id: str
    query_id: str
    issue_id: str
    related_fact_or_concept: str
    page: str | None
    chunk_id: str
    section_title: str | None
    raw_text: str
    normalized_text: str
    excerpt: str
    meeting_body: MeetingBody
    meeting_type: MeetingType
    meeting_date: str | None
    speaker_name_public: str | None
    speaker_role: SpeakerRole
    passage_nature: PassageNature
    subject_tags: tuple[str, ...]
    matched_concepts: tuple[str, ...]
    semantic_score: float
    lexical_score: float
    final_score: float
    confidence: str
    sensitive: bool
    context_before: str | None
    context_after: str | None
    qualification_reason: str
    limitations: tuple[str, ...]
    proves: str
    does_not_prove: str
    legal_value: str
    redacted: bool = False

    def __post_init__(self) -> None:
        required = (
            self.passage_id,
            self.document_id,
            self.query_id,
            self.issue_id,
            self.related_fact_or_concept,
            self.chunk_id,
            self.raw_text,
            self.normalized_text,
            self.excerpt,
            self.confidence,
            self.qualification_reason,
            self.proves,
            self.does_not_prove,
            self.legal_value,
        )
        if not all(str(value).strip() for value in required):
            raise ValueError("PV passage identity, text and qualification are required")
        if any(not 0 <= score <= 1 for score in (
            self.semantic_score,
            self.lexical_score,
            self.final_score,
        )):
            raise ValueError("PV passage scores must be between zero and one")
        if NOT_A_LEGAL_NORM not in self.does_not_prove:
            raise ValueError("a PV passage must explicitly deny automatic normative value")

    def to_dict(self, *, public: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        payload["meeting_body"] = self.meeting_body.value
        payload["meeting_type"] = self.meeting_type.value
        payload["speaker_role"] = self.speaker_role.value
        payload["passage_nature"] = self.passage_nature.value
        if public:
            payload.pop("raw_text", None)
            payload.pop("normalized_text", None)
            payload.pop("chunk_id", None)
            payload.pop("passage_id", None)
            payload.pop("document_id", None)
            payload.pop("query_id", None)
            payload.pop("issue_id", None)
            payload["excerpt"] = redact_public_value(self.excerpt, max_length=700)
            payload["context_before"] = redact_public_value(self.context_before, max_length=240)
            payload["context_after"] = redact_public_value(self.context_after, max_length=240)
            payload["speaker_name_public"] = redact_public_value(
                self.speaker_name_public, max_length=80
            )
        return payload


@dataclass(frozen=True, slots=True)
class PVSearchQuery:
    query_id: str
    issue_id: str
    target_id: str
    case_session_id: str
    concepts: tuple[str, ...]
    variants: tuple[str, ...]
    exact_phrases: tuple[str, ...]
    negative_terms: tuple[str, ...]
    temporal_scope: str
    body_scope: tuple[MeetingBody, ...]
    establishment_scope: str
    document_types: tuple[str, ...]
    min_score: float
    max_results: int
    purpose: str
    blocked: bool
    reason: str

    def __post_init__(self) -> None:
        required = (
            self.query_id,
            self.issue_id,
            self.target_id,
            self.case_session_id,
            self.establishment_scope,
            self.purpose,
            self.reason,
        )
        if not all(value.strip() for value in required):
            raise ValueError("PV search query identity and scope are required")
        if not self.concepts or not self.document_types:
            raise ValueError("PV search concepts and document types are required")
        if not 0 <= self.min_score <= 1 or self.max_results < 1:
            raise ValueError("invalid PV search threshold or result limit")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["body_scope"] = [item.value for item in self.body_scope]
        return payload


@dataclass(frozen=True, slots=True)
class PVSearchExecution:
    execution_id: str
    query_id: str
    corpus_root_status: str
    documents_available: int
    documents_scanned: int
    chunks_scanned: int
    passages_matched: int
    passages_retained: int
    started_at: str
    completed_at: str
    duration_ms: int
    search_mode: SearchMode
    searched_concepts: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    results: tuple[PVPassage, ...]
    documents: tuple[PVDocument, ...] = ()
    rejected_reasons: tuple[tuple[str, int], ...] = ()
    date_range: str | None = None

    def __post_init__(self) -> None:
        counters = (
            self.documents_available,
            self.documents_scanned,
            self.chunks_scanned,
            self.passages_matched,
            self.passages_retained,
            self.duration_ms,
        )
        if min(counters) < 0 or self.passages_retained != len(self.results):
            raise ValueError("PV execution counters are inconsistent")

    def to_dict(self, *, public: bool = False) -> dict[str, Any]:
        if public:
            return {
                "title": "Recherche dans les PV CSE/CSSCT",
                "search_executed": self.corpus_root_status == "AVAILABLE",
                "corpus_available": self.documents_available,
                "documents_examined": self.documents_scanned,
                "period": self.date_range,
                "themes": list(self.searched_concepts),
                "results_retained": self.passages_retained,
                "results": [item.to_dict(public=True) for item in self.results],
                "message": (
                    None
                    if self.results
                    else "Aucun passage suffisamment pertinent retrouvé dans les PV "
                    "CSE/CSSCT indexés. Cette absence de résultat ne prouve pas une "
                    "absence d’information ou de consultation."
                ),
                "corpus_limits": [
                    redact_public_value(item, max_length=240) for item in self.warnings
                ],
                "legal_scope": NOT_A_LEGAL_NORM,
            }
        payload = asdict(self)
        payload["search_mode"] = self.search_mode.value
        payload["results"] = [item.to_dict() for item in self.results]
        payload["documents"] = [item.to_dict() for item in self.documents]
        return payload


__all__ = (
    "MeetingBody",
    "MeetingType",
    "NOT_A_LEGAL_NORM",
    "PVDocument",
    "PVPassage",
    "PVSearchExecution",
    "PVSearchQuery",
    "PassageNature",
    "SearchMode",
    "SpeakerRole",
)
