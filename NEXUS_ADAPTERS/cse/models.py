"""Immutable translation inputs, outputs and diagnostics for CSE Memory."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from automation.cse_memory.document_models import DocumentRecord
from automation.cse_memory.metadata_models import MetadataRecord
from NEXUS_CORE import DocumentReference, EmploymentPeriod, EntityReference, Evidence, Finding, Recommendation
from NEXUS_CORE.identifiers import EntityId
from NEXUS_CORE.reasoning import ConfidenceAssessment, ReasoningConflict


class CSEDecisionRole(str, Enum):
    """Declared translation role; it is input metadata, not inferred business logic."""

    FINDING = "FINDING"
    RECOMMENDATION = "RECOMMENDATION"
    FINDING_AND_RECOMMENDATION = "FINDING_AND_RECOMMENDATION"


@dataclass(frozen=True, slots=True)
class CSEMeetingSnapshot:
    meeting_id: str
    meeting_date: date
    instance_code: str
    agenda_items: tuple[str, ...] = ()
    participant_references: tuple[str, ...] = ()
    document_ids: tuple[str, ...] = ()
    related_minutes_ids: tuple[str, ...] = ()
    confidence: float = 0.0


@dataclass(frozen=True, slots=True)
class CSEDecisionSnapshot:
    decision_id: str
    meeting_id: str
    role: CSEDecisionRole
    decision_code: str
    description: str
    document_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CSEVoteSnapshot:
    vote_id: str
    meeting_id: str
    result_code: str
    votes_for: int
    votes_against: int
    abstentions: int
    decision_id: str | None = None
    document_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CSEAdapterDiagnostics:
    code: str
    category: str
    severity: str
    technical_reference: EntityId | None = None
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        for value in (self.code, self.category, self.severity):
            if not value or not value.replace("_", "").isalnum():
                raise ValueError("diagnostics must contain technical codes only")


@dataclass(frozen=True, slots=True)
class CSEAdapterInput:
    subject: EntityReference
    produced_at: datetime
    documents: tuple[DocumentRecord, ...] = ()
    metadata_records: tuple[MetadataRecord, ...] = ()
    meetings: tuple[CSEMeetingSnapshot, ...] = ()
    decisions: tuple[CSEDecisionSnapshot, ...] = ()
    votes: tuple[CSEVoteSnapshot, ...] = ()
    source_schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class CSEAdapterResult:
    evidence: tuple[Evidence, ...]
    findings: tuple[Finding, ...]
    recommendations: tuple[Recommendation, ...]
    documents: tuple[DocumentReference, ...]
    employment_periods: tuple[EmploymentPeriod, ...]
    reasoning_conflicts: tuple[ReasoningConflict, ...]
    confidence: ConfidenceAssessment
    diagnostics: tuple[CSEAdapterDiagnostics, ...]
    source_schema_version: str
    schema_version: str = "1.0"
