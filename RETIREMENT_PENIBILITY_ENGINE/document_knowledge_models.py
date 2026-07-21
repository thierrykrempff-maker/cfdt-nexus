"""Immutable metadata models for future retirement document knowledge.

The models describe what should be consulted.  They never contain document
content and perform no legal, C2P or retirement calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DocumentPriority(str, Enum):
    """Qualitative selection priority without a numeric score."""

    REQUIRED = "REQUIRED"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    CONTEXTUAL = "CONTEXTUAL"


class DocumentValidity(str, Enum):
    """Declared temporal state of a document version."""

    ACTIVE = "ACTIVE"
    FUTURE = "FUTURE"
    EXPIRED = "EXPIRED"
    REPEALED = "REPEALED"
    SUPERSEDED = "SUPERSEDED"
    UNKNOWN = "UNKNOWN"


class DocumentRelationshipType(str, Enum):
    """Relationships between documentary metadata records."""

    SUPERSEDES = "SUPERSEDES"
    REPLACES = "REPLACES"
    AMENDS = "AMENDS"
    IMPLEMENTS = "IMPLEMENTS"
    INTERPRETS = "INTERPRETS"
    COMPLEMENTS = "COMPLEMENTS"
    REFERENCES = "REFERENCES"


@dataclass(frozen=True)
class DocumentPeriod:
    """Declared applicability interval using ISO calendar dates."""

    valid_from: str | None
    valid_to: str | None


@dataclass(frozen=True)
class DocumentVersion:
    """One metadata-only version in a documentary timeline."""

    version_id: str
    document_id: str
    label: str
    period: DocumentPeriod
    validity: DocumentValidity
    version_date: str | None = None
    provenance: str = ""


@dataclass(frozen=True)
class DocumentRelationship:
    """Directed relation between document or version identifiers."""

    relationship_id: str
    source_id: str
    target_id: str
    relationship_type: DocumentRelationshipType


@dataclass(frozen=True)
class DocumentTimeline:
    """Ordered declarations for successive versions of one document family."""

    document_family_id: str
    versions: tuple[DocumentVersion, ...] = ()
    relationships: tuple[DocumentRelationship, ...] = ()


@dataclass(frozen=True)
class ApplicablePassage:
    """Opaque passage locator without copied text."""

    passage_id: str
    document_id: str
    version_id: str | None
    locator: str
    provenance: str


@dataclass(frozen=True)
class ApplicableDocument:
    """Metadata candidate that a future provider may make available."""

    document_id: str
    title: str
    document_type: str
    source_id: str
    priority: DocumentPriority
    authority_level: str
    domains: tuple[str, ...] = ()
    version: DocumentVersion | None = None
    passages: tuple[ApplicablePassage, ...] = ()
    individual_evidence_required: bool = True
    provenance: str = ""


@dataclass(frozen=True)
class KnowledgeRequest:
    """Synthetic selection criteria derived from one career question."""

    request_id: str
    event_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    classification: str | None = None
    job_position: str | None = None
    work_schedule: str | None = None
    night_work: bool = False
    five_shift_work: bool = False
    seniority_context: bool = False
    atmp_context: bool = False
    c2p_context: bool = False
    end_of_career_context: bool = False
    retirement_context: bool = False
    keywords: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextualDocumentSet:
    """Selected metadata grouped by purpose, without opening documents."""

    required: tuple[ApplicableDocument, ...] = ()
    supporting: tuple[ApplicableDocument, ...] = ()
    contextual: tuple[ApplicableDocument, ...] = ()


@dataclass(frozen=True)
class KnowledgeContext:
    """References prepared from timeline, evidence and a worker question."""

    context_id: str
    timeline_id: str
    event_ids: tuple[str, ...]
    evidence_bundle_id: str
    evidence_ids: tuple[str, ...]
    question: str
    request: KnowledgeRequest
    selected_documents: ContextualDocumentSet = ContextualDocumentSet()
    synthetic_only: bool = True


@dataclass(frozen=True)
class DocumentSelectionReport:
    """Explainable plan of document families to consult later."""

    request_id: str
    required_document_families: tuple[str, ...]
    reasons: tuple[str, ...]
    selected_documents: ContextualDocumentSet
    opened_document_ids: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class KnowledgeResult:
    """Architecture-level result containing selection and version metadata."""

    request: KnowledgeRequest
    selection_report: DocumentSelectionReport
    applicable_versions: tuple[DocumentVersion, ...] = ()
    rule_candidate_ids: tuple[str, ...] = ()
