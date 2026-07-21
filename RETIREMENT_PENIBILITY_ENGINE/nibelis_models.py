"""Immutable metadata-only models for synthetic Nibelis exports."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .career_import_models import ImportBatch
from .career_reconstruction_models import ReconstructionProposal


class NibelisConfidence(str, Enum):
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class NibelisStatus(str, Enum):
    EMPTY = "EMPTY"
    DRAFT = "DRAFT"
    VALID = "VALID"
    INVALID = "INVALID"
    READY_FOR_IMPORT = "READY_FOR_IMPORT"


class NibelisReportView(str, Enum):
    EMPLOYEE_VIEW = "EMPLOYEE_VIEW"
    EXPERT_VIEW = "EXPERT_VIEW"


class NibelisReferentialLookup(Protocol):
    """Identifier-only adapter to existing CFDT Nexus payroll referentials."""

    def contains_rubric(self, rubric_id: str) -> bool: ...

    def contains_parameter(self, parameter_id: str) -> bool: ...


@dataclass(frozen=True)
class NibelisMetadata:
    export_id: str
    source_reference: str
    imported_at: str
    version: str
    confidence: NibelisConfidence
    synthetic_only: bool = True


@dataclass(frozen=True)
class NibelisEmployer:
    employer_id: str
    label: str | None
    source_reference: str


@dataclass(frozen=True)
class NibelisPayrollPeriod:
    period_id: str
    employer_id: str
    start_date: str | None
    end_date: str | None


@dataclass(frozen=True)
class NibelisSalaryItem:
    """Export occurrence linked to an existing rubric, not a rubric model."""

    item_id: str
    period_id: str
    referential_rubric_id: str
    declared_amount: str | None = None
    declared_base: str | None = None
    declared_rate: str | None = None
    declared_quantity: str | None = None


@dataclass(frozen=True)
class NibelisContribution:
    contribution_id: str
    period_id: str
    referential_rubric_id: str
    declared_amount: str | None = None


@dataclass(frozen=True)
class NibelisPayrollParameter:
    parameter_id: str
    period_id: str
    referential_parameter_id: str
    declared_value: str | None = None


@dataclass(frozen=True)
class NibelisClassification:
    classification_id: str
    period_id: str
    label: str | None


@dataclass(frozen=True)
class NibelisCoefficient:
    coefficient_id: str
    classification_id: str
    value: str | None


@dataclass(frozen=True)
class NibelisEvidence:
    evidence_id: str
    evidence_type: str
    opaque_reference: str


@dataclass(frozen=True)
class NibelisExport:
    """Complete synthetic export; no payslip or export content is stored."""

    metadata: NibelisMetadata
    employer: NibelisEmployer | None = None
    periods: tuple[NibelisPayrollPeriod, ...] = ()
    salary_items: tuple[NibelisSalaryItem, ...] = ()
    contributions: tuple[NibelisContribution, ...] = ()
    parameters: tuple[NibelisPayrollParameter, ...] = ()
    classifications: tuple[NibelisClassification, ...] = ()
    coefficients: tuple[NibelisCoefficient, ...] = ()
    evidence: tuple[NibelisEvidence, ...] = ()
    status: NibelisStatus = NibelisStatus.DRAFT


@dataclass(frozen=True)
class NibelisIssue:
    issue_id: str
    issue_type: str
    subject_ids: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class NibelisWarning:
    warning_id: str
    description: str


@dataclass(frozen=True)
class NibelisValidation:
    valid: bool
    status: NibelisStatus
    issues: tuple[NibelisIssue, ...] = ()
    warnings: tuple[NibelisWarning, ...] = ()


@dataclass(frozen=True)
class NibelisPayrollInformation:
    period_ids: tuple[str, ...]
    rubric_ids: tuple[str, ...]
    salary_item_ids: tuple[str, ...]
    contribution_ids: tuple[str, ...]
    parameter_ids: tuple[str, ...]
    classifications: tuple[str, ...]
    coefficients: tuple[str, ...]


@dataclass(frozen=True)
class NibelisImport:
    export_id: str
    import_batch: ImportBatch
    converted_record_ids: tuple[str, ...]
    reconstruction_proposal: ReconstructionProposal | None = None


@dataclass(frozen=True)
class NibelisSummary:
    export_id: str
    status: NibelisStatus
    periods: int
    salary_items: int
    contributions: int
    issues: int
    requires_human_review: bool = True


@dataclass(frozen=True)
class NibelisReport:
    view: NibelisReportView
    summary: NibelisSummary
    recognized_periods: tuple[str, ...]
    detected_rubrics: tuple[str, ...]
    remuneration_elements: tuple[str, ...]
    points_to_verify: tuple[str, ...]
    provenance: tuple[str, ...] = ()
    rubrics: tuple[str, ...] = ()
    contributions: tuple[str, ...] = ()
    classifications: tuple[str, ...] = ()
    parameters: tuple[str, ...] = ()
    career_import_preparation: tuple[str, ...] = ()
