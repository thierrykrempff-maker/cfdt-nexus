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
from .working_time_articulation import articulate_syndical_domains
from .working_time_engine import (
    WorkingTimeReasoningEngine,
    needs_working_time_reasoning,
)
from .working_time_models import (
    DocumentComparison,
    DomainArticulation,
    EvidenceCategory,
    OnCallObservation,
    PayImpactLikelihood,
    PotentialPayImpact,
    QuestionPriority,
    ScheduleKind,
    ScheduleObservation,
    WorkingOrganization,
    WorkingTimeAnalysis,
    WorkingTimeEvidence,
    WorkingTimeQualification,
    WorkingTimeQuestion,
    WorkingTimeSituation,
    WorkingTimeStrategy,
)
from .working_time_scenarios import working_time_scenarios

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
    "DocumentComparison",
    "DomainArticulation",
    "EvidenceCategory",
    "EvidencePriority",
    "EvidenceRequirement",
    "FactStatus",
    "OnCallObservation",
    "PayImpactLikelihood",
    "PotentialPayImpact",
    "PROTOCOL_STEPS",
    "PositionAnalysis",
    "ProtectedEmployeeAnalysis",
    "PrioritizedQuestion",
    "REFERENCE_QUESTION",
    "ReasoningStep",
    "QualificationCandidate",
    "QuestionPriority",
    "SourceAssessment",
    "SourceContradiction",
    "SourceReference",
    "SourceVerification",
    "ScheduleKind",
    "ScheduleObservation",
    "SyndicalCaseInput",
    "SyndicalReasoningEngine",
    "SyndicalReasoningReport",
    "UrgencyLevel",
    "WorkingOrganization",
    "WorkingTimeAnalysis",
    "WorkingTimeEvidence",
    "WorkingTimeQualification",
    "WorkingTimeQuestion",
    "WorkingTimeReasoningEngine",
    "WorkingTimeSituation",
    "WorkingTimeStrategy",
    "articulate_syndical_domains",
    "build_reference_case",
    "contract_change_scenarios",
    "disciplinary_scenarios",
    "needs_contract_change_reasoning",
    "needs_disciplinary_reasoning",
    "needs_working_time_reasoning",
    "working_time_scenarios",
)
