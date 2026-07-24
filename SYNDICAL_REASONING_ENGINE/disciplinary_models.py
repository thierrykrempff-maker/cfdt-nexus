"""Immutable R1B contracts for disciplinary reasoning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contract_change_models import (
    ContractChangeStrategy,
    EvidenceRequirement,
    PositionAnalysis,
    PrioritizedQuestion,
)
from .models import SyndicalReasoningReport


class DisciplinaryQualification(str, Enum):
    INFORMAL_REMINDER = "informal_reminder"
    WARNING = "warning"
    REPRIMAND = "reprimand"
    DISCIPLINARY_SUSPENSION = "disciplinary_suspension"
    DISCIPLINARY_TRANSFER = "disciplinary_transfer"
    DISCIPLINARY_DEMOTION = "disciplinary_demotion"
    DISMISSAL_SIMPLE_MISCONDUCT = "dismissal_simple_misconduct"
    DISMISSAL_GROSS_MISCONDUCT = "dismissal_gross_misconduct"
    DISMISSAL_WILFUL_MISCONDUCT = "dismissal_wilful_misconduct"
    PROFESSIONAL_INSUFFICIENCY = "professional_insufficiency"
    INSUFFICIENT_RESULTS = "insufficient_results"
    JOB_ABANDONMENT = "job_abandonment"
    REFUSAL_CONTRACT_CHANGE = "refusal_contract_change"
    PROTECTED_EMPLOYEE = "protected_employee"
    UNDETERMINED_MEASURE = "undetermined_measure"


@dataclass(frozen=True, slots=True)
class DisciplinaryQualificationCandidate:
    qualification: DisciplinaryQualification
    rationale: str
    decisive_information: tuple[str, ...]
    provisional: bool = True


@dataclass(frozen=True, slots=True)
class ProtectedEmployeeAnalysis:
    protection_possible: bool
    checks: tuple[str, ...]
    cautions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DisciplinaryAnalysis:
    base_report: SyndicalReasoningReport
    qualification_candidates: tuple[DisciplinaryQualificationCandidate, ...]
    procedure_checks: tuple[str, ...]
    automatic_questions: tuple[PrioritizedQuestion, ...]
    employee_position: PositionAnalysis
    employer_position: PositionAnalysis
    evidence: tuple[EvidenceRequirement, ...]
    strategies: tuple[ContractChangeStrategy, ...]
    protected_employee: ProtectedEmployeeAnalysis
    scenario_code: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "analysis_type": "disciplinary_procedure",
            "qualification_candidates": [
                {
                    "qualification": item.qualification.value,
                    "rationale": item.rationale,
                    "decisive_information": list(item.decisive_information),
                    "provisional": item.provisional,
                }
                for item in self.qualification_candidates
            ],
            "procedure_checks": list(self.procedure_checks),
            "automatic_questions": [
                {
                    "priority": item.priority,
                    "question": item.question,
                    "purpose": item.purpose,
                }
                for item in self.automatic_questions
            ],
            "employee_position": {
                "favorable_arguments": list(self.employee_position.favorable_arguments),
                "possible_irregularities": list(self.employee_position.strengths),
                "weaknesses_or_points_to_prove": list(
                    self.employee_position.weaknesses_or_points_to_prove
                ),
            },
            "employer_position": {
                "possible_arguments": list(self.employer_position.favorable_arguments),
                "possible_justifications": list(self.employer_position.strengths),
                "elements_to_prove": list(
                    self.employer_position.weaknesses_or_points_to_prove
                ),
            },
            "evidence": [
                {
                    "document_type": item.document_type,
                    "label": item.label,
                    "priority": item.priority.value,
                    "purpose": item.purpose,
                }
                for item in self.evidence
            ],
            "strategies": [
                {
                    "order": item.order,
                    "name": item.name,
                    "objective": item.objective,
                    "advantages": list(item.advantages),
                    "limitations": list(item.limitations),
                    "risks": list(item.risks),
                    "required_pieces": list(item.required_pieces),
                    "urgency": item.urgency.value,
                }
                for item in self.strategies
            ],
            "protected_employee": {
                "protection_possible": self.protected_employee.protection_possible,
                "checks": list(self.protected_employee.checks),
                "cautions": list(self.protected_employee.cautions),
            },
            "scenario_code": self.scenario_code,
        }
