"""Public API of the Syndical Reasoning Engine R0."""

from .engine import SyndicalReasoningEngine
from .models import (
    ActionOption,
    ActionPlanStep,
    AvailablePiece,
    CaseFact,
    Citation,
    ConfidentialityLevel,
    ConfidenceLevel,
    FactStatus,
    SourceAssessment,
    SourceContradiction,
    SourceReference,
    SourceVerification,
    SyndicalCaseInput,
    SyndicalReasoningReport,
    UrgencyLevel,
)
from .protocol import PROTOCOL_STEPS, ReasoningStep
from .reference_scenario import REFERENCE_QUESTION, build_reference_case
from .contract_change_engine import (
    ContractChangeReasoningEngine,
    needs_contract_change_reasoning,
)
from .contract_change_models import (
    ChangeDimension,
    ContractChangeAnalysis,
    ContractChangeStrategy,
    EvidencePriority,
    EvidenceRequirement,
    PositionAnalysis,
    PrioritizedQuestion,
    QualificationCandidate,
)
from .contract_change_scenarios import contract_change_scenarios
from .disciplinary_engine import (
    DisciplinaryReasoningEngine,
    needs_disciplinary_reasoning,
)
from .disciplinary_models import (
    DisciplinaryAnalysis,
    DisciplinaryQualification,
    DisciplinaryQualificationCandidate,
    ProtectedEmployeeAnalysis,
)
from .disciplinary_scenarios import disciplinary_scenarios

__all__ = (
    "ActionOption",
    "ActionPlanStep",
    "AvailablePiece",
    "CaseFact",
    "Citation",
    "ChangeDimension",
    "ConfidentialityLevel",
    "ConfidenceLevel",
    "ContractChangeAnalysis",
    "ContractChangeReasoningEngine",
    "ContractChangeStrategy",
    "DisciplinaryAnalysis",
    "DisciplinaryQualification",
    "DisciplinaryQualificationCandidate",
    "DisciplinaryReasoningEngine",
    "EvidencePriority",
    "EvidenceRequirement",
    "FactStatus",
    "PROTOCOL_STEPS",
    "PositionAnalysis",
    "ProtectedEmployeeAnalysis",
    "PrioritizedQuestion",
    "REFERENCE_QUESTION",
    "ReasoningStep",
    "QualificationCandidate",
    "SourceAssessment",
    "SourceContradiction",
    "SourceReference",
    "SourceVerification",
    "SyndicalCaseInput",
    "SyndicalReasoningEngine",
    "SyndicalReasoningReport",
    "UrgencyLevel",
    "build_reference_case",
    "contract_change_scenarios",
    "disciplinary_scenarios",
    "needs_contract_change_reasoning",
    "needs_disciplinary_reasoning",
)
