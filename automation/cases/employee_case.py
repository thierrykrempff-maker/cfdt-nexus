#!/usr/bin/env python
"""Data model for synthetic employee cases (LOT 5A)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class DocumentType(str, Enum):
    PAYSLIP = "payslip"
    TIME_STATEMENT = "time_statement"
    PLANNING = "planning"
    EMPLOYMENT_CONTRACT = "employment_contract"
    CONTRACT_AMENDMENT = "contract_amendment"
    COMPANY_AGREEMENT = "company_agreement"
    COLLECTIVE_AGREEMENT = "collective_agreement"
    HR_CORRESPONDENCE = "hr_correspondence"
    MANAGER_DECISION = "manager_decision"
    ANONYMIZED_ABSENCE_PROOF = "anonymized_absence_proof"
    LEAVE_REQUEST = "leave_request"
    BONUS_NOTIFICATION = "bonus_notification"
    CSE_DOCUMENT = "cse_document"
    ON_CALL_STATEMENT = "on_call_statement"
    INTERVENTION_STATEMENT = "intervention_statement"
    IJSS_STATEMENT = "ijss_statement"
    JOB_DESCRIPTION = "job_description"
    FUNCTIONS_STATEMENT = "functions_statement"
    LEAVE_COUNTER = "leave_counter"
    ACQUISITION_PERIOD = "acquisition_period"
    APPLICABLE_RULE = "applicable_rule"
    OTHER = "other"


class AvailabilityStatus(str, Enum):
    PRESENT = "present"
    MISSING = "missing"
    UNAVAILABLE = "unavailable"


class ConfidentialityLevel(str, Enum):
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    SENSITIVE = "sensitive"


class ControlStatus(str, Enum):
    NOT_CHECKED = "not_checked"
    CHECKED = "checked"
    WARNING = "warning"
    BLOCKED = "blocked"


class CaseStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    WARNING = "warning"
    BLOCKED = "blocked"
    FAILED = "failed"


class ExpertStatus(str, Enum):
    COMPLETED = "completed"
    WARNING = "warning"
    REFUSED = "refused"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


@dataclass(frozen=True)
class EmployeeDocument:
    document_id: str
    document_type: DocumentType
    title: str
    period: str | None
    declared_source: str
    file_format: str
    availability: AvailabilityStatus = AvailabilityStatus.PRESENT
    confidentiality: ConfidentialityLevel = ConfidentialityLevel.INTERNAL
    control_status: ControlStatus = ControlStatus.NOT_CHECKED
    synthetic_summary: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    synthetic_only: bool = True

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for key in ("document_type", "availability", "confidentiality", "control_status"):
            result[key] = getattr(self, key).value
        return result


@dataclass(frozen=True)
class PipelineHistoryEntry:
    step: str
    status: StepStatus
    message: str


@dataclass
class EmployeeCase:
    case_id: str
    title: str
    main_question: str
    description: str
    period: str
    population: str
    detected_themes: list[str]
    urgent: bool
    status: CaseStatus
    documents: list[EmployeeDocument]
    missing_documents: list[str] = field(default_factory=list)
    employee_information: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    confidentiality: ConfidentialityLevel = ConfidentialityLevel.RESTRICTED
    synthetic_only: bool = True
    created_at: str = "2099-01-01T09:00:00Z"
    history: list[PipelineHistoryEntry] = field(default_factory=list)
    privacy_probe: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "title": self.title,
            "main_question": self.main_question,
            "description": self.description,
            "period": self.period,
            "population": self.population,
            "detected_themes": list(self.detected_themes),
            "urgent": self.urgent,
            "status": self.status.value,
            "documents": [document.as_dict() for document in self.documents],
            "missing_documents": list(self.missing_documents),
            "employee_information": dict(self.employee_information),
            "assumptions": list(self.assumptions),
            "confidentiality": self.confidentiality.value,
            "synthetic_only": self.synthetic_only,
            "created_at": self.created_at,
            "history": [
                {"step": item.step, "status": item.status.value, "message": item.message}
                for item in self.history
            ],
            "privacy_probe": self.privacy_probe,
        }


@dataclass(frozen=True)
class ExpertAnalysis:
    expert: str
    status: ExpertStatus
    summary: str
    findings: tuple[str, ...] = ()
    cited_rules_or_sources: tuple[str, ...] = ()
    documents_used: tuple[str, ...] = ()
    missing_documents: tuple[str, ...] = ()
    control_points: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    confidence: str = "UNKNOWN"
    refusal_reason: str | None = None
    limits: tuple[str, ...] = ()
    period: str | None = None
    asserted_facts: dict[str, str] = field(default_factory=dict)
