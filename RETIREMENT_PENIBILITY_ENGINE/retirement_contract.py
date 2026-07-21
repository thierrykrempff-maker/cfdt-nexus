"""Public contracts for the architecture-only retirement foundation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .retirement_models import (
    EmployeeCareer,
    EvidenceItem,
    MissingInformation,
    RetirementConfidence,
    RetirementReport,
)


@dataclass(frozen=True)
class RetirementQuestion:
    """A worker question identified by opaque, non-nominative references."""

    question_id: str
    question_text: str
    employee_case_id: str | None = None
    requested_topics: tuple[str, ...] = ()
    explicit_consent: bool = False
    synthetic_only: bool = True


@dataclass(frozen=True)
class RetirementRequest:
    """Normalized input combining a question, career and available evidence."""

    request_id: str
    question: RetirementQuestion
    career: EmployeeCareer | None
    available_evidence: tuple[EvidenceItem, ...] = ()


@dataclass(frozen=True)
class RetirementResponse:
    """Public output contract preserving report, evidence and uncertainty."""

    report: RetirementReport
    evidence_used: tuple[EvidenceItem, ...]
    confidence: RetirementConfidence
    missing_information: tuple[MissingInformation, ...]


class RetirementAssessmentPort(Protocol):
    """Future business implementation boundary; no implementation in LOT 1."""

    def assess(self, request: RetirementRequest) -> RetirementResponse: ...


@dataclass(frozen=True)
class RetirementFoundationContract:
    """Declarative safety contract for the inactive domain foundation."""

    domain_id: str = "RETIREMENT_PENIBILITY_ENGINE"
    status: str = "ARCHITECTURE_ONLY"
    enabled: bool = False
    performs_calculation: bool = False
    performs_simulation: bool = False
    network_allowed: bool = False
    scraping_allowed: bool = False
    download_allowed: bool = False
    real_documents_allowed: bool = False
    administrative_validation_required: bool = True


RETIREMENT_FOUNDATION_CONTRACT = RetirementFoundationContract()
