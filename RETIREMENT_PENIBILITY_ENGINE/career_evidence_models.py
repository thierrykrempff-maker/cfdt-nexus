"""Immutable models for sourced career evidence and explainable reports.

Only opaque references and synthetic metadata are represented.  Document
content, medical detail, personal identifiers and local paths are excluded.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import NewType


EvidenceId = NewType("EvidenceId", str)


class EvidenceSourceType(str, Enum):
    """Declared documentary source families."""

    OFFICIAL_RETIREMENT_RECORD = "OFFICIAL_RETIREMENT_RECORD"
    CARSAT_NOTIFICATION = "CARSAT_NOTIFICATION"
    CNAV_NOTIFICATION = "CNAV_NOTIFICATION"
    C2P_NOTIFICATION = "C2P_NOTIFICATION"
    SOCIAL_SECURITY_DOCUMENT = "SOCIAL_SECURITY_DOCUMENT"
    EMPLOYMENT_CONTRACT = "EMPLOYMENT_CONTRACT"
    EMPLOYMENT_AMENDMENT = "EMPLOYMENT_AMENDMENT"
    PAYSLIP = "PAYSLIP"
    EMPLOYER_CERTIFICATE = "EMPLOYER_CERTIFICATE"
    WORK_SCHEDULE = "WORK_SCHEDULE"
    KELIO_EXPORT = "KELIO_EXPORT"
    NIBELIS_EXPORT = "NIBELIS_EXPORT"
    INEOS_AGREEMENT = "INEOS_AGREEMENT"
    COLLECTIVE_AGREEMENT = "COLLECTIVE_AGREEMENT"
    INTERNAL_CSE_DOCUMENT = "INTERNAL_CSE_DOCUMENT"
    INTERNAL_CSSCT_DOCUMENT = "INTERNAL_CSSCT_DOCUMENT"
    MEDICAL_OR_ATMP_NOTIFICATION = "MEDICAL_OR_ATMP_NOTIFICATION"
    EMPLOYEE_DECLARATION = "EMPLOYEE_DECLARATION"
    OTHER_DOCUMENT = "OTHER_DOCUMENT"


class EvidenceAuthorityLevel(str, Enum):
    """Institutional authority, distinct from factual confidence."""

    AUTHORITATIVE_OFFICIAL = "AUTHORITATIVE_OFFICIAL"
    AUTHORITATIVE_EMPLOYER = "AUTHORITATIVE_EMPLOYER"
    CONTRACTUAL = "CONTRACTUAL"
    CORROBORATING = "CORROBORATING"
    CONTEXTUAL = "CONTEXTUAL"
    DECLARATIVE_ONLY = "DECLARATIVE_ONLY"


class EvidenceConfidenceLevel(str, Enum):
    """Prudential confidence label without fixed percentage."""

    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EvidenceStatus(str, Enum):
    """Lifecycle state retained with the documentary reference."""

    PROVIDED = "PROVIDED"
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTED = "CONTRADICTED"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"
    MISSING = "MISSING"
    RESTRICTED = "RESTRICTED"
    REJECTED = "REJECTED"


class EvidenceRelationType(str, Enum):
    """Directed relationships supported by the evidence graph."""

    SUPPORTS = "SUPPORTS"
    PARTIALLY_SUPPORTS = "PARTIALLY_SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    REPLACES = "REPLACES"
    CORROBORATES = "CORROBORATES"
    CONTEXTUALIZES = "CONTEXTUALIZES"
    REQUIRES = "REQUIRES"
    MISSING_FOR = "MISSING_FOR"
    DERIVED_FROM = "DERIVED_FROM"
    GOVERNED_BY = "GOVERNED_BY"


class EvidenceClaimType(str, Enum):
    """Nature of a claim, kept separate for prudent resolution."""

    COLLECTIVE_RULE = "COLLECTIVE_RULE"
    INDIVIDUAL_FACT = "INDIVIDUAL_FACT"
    DECLARATION = "DECLARATION"
    OFFICIAL_FINDING = "OFFICIAL_FINDING"


class EvidenceResolutionState(str, Enum):
    """Non-judicial state produced by the prudent resolver."""

    CONFIRMED = "CONFIRMED"
    PARTIALLY_CONFIRMED = "PARTIALLY_CONFIRMED"
    UNCONFIRMED = "UNCONFIRMED"
    CONFLICTED = "CONFLICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    REQUIRES_OFFICIAL_VALIDATION = "REQUIRES_OFFICIAL_VALIDATION"


class EvidenceReportView(str, Enum):
    """Audience-specific report projection."""

    EMPLOYEE_VIEW = "EMPLOYEE_VIEW"
    EXPERT_VIEW = "EXPERT_VIEW"


@dataclass(frozen=True)
class DocumentPassageReference:
    """Minimal passage locator; it never embeds the document or full text."""

    passage_id: str
    document_id: str
    locator: str
    excerpt_reference: str | None = None
    provenance: str = ""


@dataclass(frozen=True)
class EvidenceReference:
    """Minimal documentary reference with provenance and no document content."""

    evidence_id: EvidenceId
    source_type: EvidenceSourceType
    title: str
    reference: str
    provenance: str
    version_date: str | None = None
    sensitive: bool = False


@dataclass(frozen=True)
class CareerEvidenceItem:
    """Evidence metadata and assessment labels, never the underlying document."""

    reference: EvidenceReference
    authority_level: EvidenceAuthorityLevel
    confidence_level: EvidenceConfidenceLevel = EvidenceConfidenceLevel.UNKNOWN
    status: EvidenceStatus = EvidenceStatus.PROVIDED
    observed_at: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None


@dataclass(frozen=True)
class EvidenceClaim:
    """One sourced assertion about an existing event or period identifier."""

    claim_id: str
    subject_kind: str
    subject_id: str
    claim_type: EvidenceClaimType
    statement: str
    evidence_ids: tuple[EvidenceId, ...] = ()


@dataclass(frozen=True)
class EvidenceConflict:
    """Preserved incompatibility between claims or documentary references."""

    conflict_id: str
    subject_id: str
    evidence_ids: tuple[EvidenceId, ...]
    claim_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class EvidenceGap:
    """Missing documentary support linked to a career subject."""

    gap_id: str
    subject_kind: str
    subject_id: str
    expected_source_type: EvidenceSourceType | None
    description: str


@dataclass(frozen=True)
class EvidenceRelation:
    """One directed edge in the evidence graph."""

    relation_id: str
    source_kind: str
    source_id: str
    target_kind: str
    target_id: str
    relation_type: EvidenceRelationType


@dataclass(frozen=True)
class EvidenceBundle:
    """Immutable graph state for one synthetic career case."""

    bundle_id: str
    evidence: tuple[CareerEvidenceItem, ...] = ()
    claims: tuple[EvidenceClaim, ...] = ()
    conflicts: tuple[EvidenceConflict, ...] = ()
    gaps: tuple[EvidenceGap, ...] = ()
    relations: tuple[EvidenceRelation, ...] = ()
    passages: tuple[DocumentPassageReference, ...] = ()
    synthetic_only: bool = True


@dataclass(frozen=True)
class DocumentSearchRequest:
    """Abstract local search request, not an executable query."""

    event_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    job_position: str | None = None
    work_schedule: str | None = None
    classification: str | None = None
    keywords: tuple[str, ...] = ()
    domain: str | None = None
    valid_on: str | None = None


@dataclass(frozen=True)
class DocumentSearchResult:
    """Metadata-only result returned by a future local provider."""

    document_id: str
    title: str
    document_type: str
    version_date: str | None
    passage: DocumentPassageReference | None
    search_score: str
    validity_status: str
    provenance: str


@dataclass(frozen=True)
class CareerEvidenceReport:
    """Explainable, audience-safe projection of an evidence bundle."""

    view: EvidenceReportView
    subject_id: str
    claims_examined: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    contradictory_evidence: tuple[str, ...]
    contextual_evidence: tuple[str, ...]
    collective_rules: tuple[str, ...]
    missing_documents: tuple[str, ...]
    confirmation_level: EvidenceResolutionState
    official_validation_required: bool
    provenance: tuple[str, ...]
    warnings: tuple[str, ...]
    passages: tuple[str, ...] = ()
    resolution_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceResolution:
    """Resolver output preserving every item, conflict and reason."""

    state: EvidenceResolutionState
    ordered_evidence: tuple[CareerEvidenceItem, ...]
    conflicts: tuple[EvidenceConflict, ...]
    reasons: tuple[str, ...]
