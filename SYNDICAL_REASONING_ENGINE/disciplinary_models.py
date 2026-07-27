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


class DisciplinaryActCategory(str, Enum):
    TECHNICAL_ERROR = "TECHNICAL_ERROR"
    INSUBORDINATION = "INSUBORDINATION"
    ABSENCE_OR_LATENESS = "ABSENCE_OR_LATENESS"
    INSULTING_OR_INAPPROPRIATE_BEHAVIOR = "INSULTING_OR_INAPPROPRIATE_BEHAVIOR"
    THREAT_OR_VIOLENCE = "THREAT_OR_VIOLENCE"
    ALLEGED_HARASSMENT = "ALLEGED_HARASSMENT"
    MATERIAL_DAMAGE = "MATERIAL_DAMAGE"
    SAFETY_BREACH = "SAFETY_BREACH"
    IT_MISUSE = "IT_MISUSE"
    ALCOHOL_OR_DRUGS = "ALCOHOL_OR_DRUGS"
    INTERPERSONAL_CONFLICT = "INTERPERSONAL_CONFLICT"
    UNSPECIFIED_FACTS = "UNSPECIFIED_FACTS"


@dataclass(frozen=True, slots=True)
class DisciplinaryFactExtraction:
    alleged_act: str
    act_category: DisciplinaryActCategory
    exact_words_or_behavior: str | None
    target_identified: bool | None
    target_type: str | None
    location: str | None
    public_visibility: bool | None
    material_damage: bool | None
    threat_or_violence: bool | None
    repetition: bool | None
    employee_admission: bool | None
    employer_evidence: tuple[str, ...]
    context_claimed: tuple[str, ...]
    prior_warnings: bool | None
    sanction_considered: str | None
    facts_missing: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "alleged_act": self.alleged_act,
            "act_category": self.act_category.value,
            "exact_words_or_behavior": self.exact_words_or_behavior,
            "target_identified": self.target_identified,
            "target_type": self.target_type,
            "location": self.location,
            "public_visibility": self.public_visibility,
            "material_damage": self.material_damage,
            "threat_or_violence": self.threat_or_violence,
            "repetition": self.repetition,
            "employee_admission": self.employee_admission,
            "employer_evidence": list(self.employer_evidence),
            "context_claimed": list(self.context_claimed),
            "prior_warnings": self.prior_warnings,
            "sanction_considered": self.sanction_considered,
            "facts_missing": list(self.facts_missing),
        }


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
    fact_extraction: DisciplinaryFactExtraction
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
            "fact_extraction": self.fact_extraction.to_dict(),
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
