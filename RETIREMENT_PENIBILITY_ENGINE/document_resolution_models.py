"""Neutral models for fact-aware documentary resolution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .career_import_models import ImportConfidence, ImportProvenance


class DocumentRole(str, Enum):
    """Documentary role, independent from connector implementations."""

    EMPLOYMENT_CONTRACT = "EMPLOYMENT_CONTRACT"
    EMPLOYMENT_AMENDMENT = "EMPLOYMENT_AMENDMENT"
    CAREER_STATEMENT = "CAREER_STATEMENT"
    PAYSLIP = "PAYSLIP"
    KELIO = "KELIO"
    NIBELIS = "NIBELIS"
    OTHER_EVIDENCE = "OTHER_EVIDENCE"


class FactFamily(str, Enum):
    """Fact families actually represented by Career Import values."""

    EVENT_TYPE = "EVENT_TYPE"
    EMPLOYMENT_PERIOD = "EMPLOYMENT_PERIOD"
    CAREER_PERIOD = "CAREER_PERIOD"
    EMPLOYER = "EMPLOYER"
    POSITION = "POSITION"
    CLASSIFICATION = "CLASSIFICATION"
    CONTRACTUAL_CLASSIFICATION = "CONTRACTUAL_CLASSIFICATION"
    APPLIED_CLASSIFICATION = "APPLIED_CLASSIFICATION"
    COEFFICIENT = "COEFFICIENT"
    WORKING_TIME = "WORKING_TIME"
    RECORDED_WORKING_TIME = "RECORDED_WORKING_TIME"
    NIGHT_WORK = "NIGHT_WORK"
    FIVE_SHIFT = "FIVE_SHIFT"
    ON_CALL = "ON_CALL"
    INTERVENTION = "INTERVENTION"
    LEAVE = "LEAVE"
    SALARY_ITEM = "SALARY_ITEM"
    CONTRIBUTION = "CONTRIBUTION"
    OTHER = "OTHER"


class FactResolutionStatus(str, Enum):
    """Prudent outcome of resolving one fact across documentary sources."""

    RESOLVED = "RESOLVED"
    RESOLVED_WITH_WARNINGS = "RESOLVED_WITH_WARNINGS"
    CONFLICT = "CONFLICT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNSUPPORTED_FACT_TYPE = "UNSUPPORTED_FACT_TYPE"


@dataclass(frozen=True)
class FactResolution:
    """Explainable resolution retaining every source and confidence level."""

    field_name: str
    fact_family: FactFamily
    status: FactResolutionStatus
    selected_value: object | None
    selected_record_id: str | None
    candidate_record_ids: tuple[str, ...]
    document_roles: tuple[DocumentRole, ...]
    confidences: tuple[ImportConfidence, ...]
    provenance: tuple[ImportProvenance, ...]
    explanation: str


__all__ = (
    "DocumentRole",
    "FactFamily",
    "FactResolution",
    "FactResolutionStatus",
)
