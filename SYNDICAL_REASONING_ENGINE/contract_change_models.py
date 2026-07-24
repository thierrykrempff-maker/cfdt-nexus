"""Specialized immutable contracts for contract and working-condition changes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import SyndicalReasoningReport, UrgencyLevel


class ChangeDimension(str, Enum):
    CONTRACT = "employment_contract"
    WORKING_CONDITIONS = "working_conditions"
    WORKING_HOURS = "working_hours"
    DAY_TO_SHIFT = "day_to_shift"
    TEAM = "team_change"
    POSITION = "position_change"
    QUALIFICATION = "qualification_change"
    CLASSIFICATION = "classification_change"
    GEOGRAPHIC_MOBILITY = "geographic_mobility"
    POSITION_REMOVAL = "position_removal"
    REORGANIZATION = "reorganization"
    REMUNERATION = "remuneration_change"


class EvidencePriority(str, Enum):
    ESSENTIAL = "essential"
    USEFUL = "useful"
    COMPLEMENTARY = "complementary"


@dataclass(frozen=True, slots=True)
class QualificationCandidate:
    dimension: ChangeDimension
    rationale: str
    decisive_information: tuple[str, ...]
    provisional: bool = True


@dataclass(frozen=True, slots=True)
class PrioritizedQuestion:
    priority: int
    question: str
    purpose: str

    def __post_init__(self) -> None:
        if self.priority < 1 or not self.question.strip() or not self.purpose.strip():
            raise ValueError("invalid prioritized question")


@dataclass(frozen=True, slots=True)
class EvidenceRequirement:
    document_type: str
    label: str
    priority: EvidencePriority
    purpose: str


@dataclass(frozen=True, slots=True)
class PositionAnalysis:
    favorable_arguments: tuple[str, ...]
    strengths: tuple[str, ...]
    weaknesses_or_points_to_prove: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ContractChangeStrategy:
    order: int
    name: str
    objective: str
    advantages: tuple[str, ...]
    limitations: tuple[str, ...]
    risks: tuple[str, ...]
    required_pieces: tuple[str, ...]
    urgency: UrgencyLevel


@dataclass(frozen=True, slots=True)
class ContractChangeAnalysis:
    base_report: SyndicalReasoningReport
    detected_dimensions: tuple[ChangeDimension, ...]
    qualification_candidates: tuple[QualificationCandidate, ...]
    automatic_questions: tuple[PrioritizedQuestion, ...]
    employee_position: PositionAnalysis
    employer_position: PositionAnalysis
    evidence: tuple[EvidenceRequirement, ...]
    strategies: tuple[ContractChangeStrategy, ...]
    scenario_code: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "detected_dimensions": [item.value for item in self.detected_dimensions],
            "qualification_candidates": [
                {
                    "dimension": item.dimension.value,
                    "rationale": item.rationale,
                    "decisive_information": list(item.decisive_information),
                    "provisional": item.provisional,
                }
                for item in self.qualification_candidates
            ],
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
                "strengths": list(self.employee_position.strengths),
                "weaknesses_or_points_to_prove": list(
                    self.employee_position.weaknesses_or_points_to_prove
                ),
            },
            "employer_position": {
                "possible_arguments": list(self.employer_position.favorable_arguments),
                "possible_foundations": list(self.employer_position.strengths),
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
            "scenario_code": self.scenario_code,
        }
