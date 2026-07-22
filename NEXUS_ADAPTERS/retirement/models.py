"""Immutable inputs, results and safe diagnostics for the retirement adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from automation.contracts import ExpertReport
from RETIREMENT_PENIBILITY_ENGINE.career_evidence_models import EvidenceBundle
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_models import ReconstructionProposal
from RETIREMENT_PENIBILITY_ENGINE.retirement_models import RetirementReport
from RETIREMENT_PENIBILITY_ENGINE.rule_reasoning_models import ReasoningOutcome
from NEXUS_CORE import DocumentReference, EmploymentPeriod, EntityReference, Evidence, Finding, Recommendation
from NEXUS_CORE.conflict_resolution import ResolutionCandidate
from NEXUS_CORE.identifiers import EntityId
from NEXUS_CORE.reasoning import ReasoningConflict


def _technical_code(value: str, label: str) -> None:
    if not value or not value.replace("_", "").isalnum():
        raise ValueError(f"{label} must be a stable technical code")


@dataclass(frozen=True, slots=True)
class RetirementAdapterDiagnostics:
    """Non-blocking diagnostic containing technical codes only."""

    code: str
    category: str
    severity: str
    technical_reference: EntityId | None = None
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        for value in (self.code, self.category, self.severity):
            _technical_code(value, "diagnostic field")


@dataclass(frozen=True, slots=True)
class RetirementAdapterInput:
    """Outputs already produced by Retirement, never instructions to calculate."""

    report: RetirementReport
    subject: EntityReference
    produced_at: datetime
    reconstruction: ReconstructionProposal | None = None
    evidence_bundle: EvidenceBundle | None = None
    reasoning_outcome: ReasoningOutcome | None = None
    expert_report: ExpertReport | None = None
    source_schema_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class RetirementAdapterResult:
    """Complete, immutable Nexus Core projection of Retirement outputs."""

    evidence: tuple[Evidence, ...]
    findings: tuple[Finding, ...]
    recommendations: tuple[Recommendation, ...]
    documents: tuple[DocumentReference, ...]
    employment_periods: tuple[EmploymentPeriod, ...]
    reasoning_conflicts: tuple[ReasoningConflict, ...]
    resolution_candidates: tuple[ResolutionCandidate, ...]
    diagnostics: tuple[RetirementAdapterDiagnostics, ...]
    source_schema_version: str
    schema_version: str = "1.0"
