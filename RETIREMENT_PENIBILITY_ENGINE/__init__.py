"""Public API for the architecture-only Retirement & Penibility foundation."""

from .retirement_contract import (
    RETIREMENT_FOUNDATION_CONTRACT,
    RetirementAssessmentPort,
    RetirementFoundationContract,
    RetirementQuestion,
    RetirementRequest,
    RetirementResponse,
)
from .retirement_evidence_matrix import (
    EVIDENCE_MATRIX,
    EVIDENCE_WEIGHTING_RULES,
    EvidenceRequirement,
)
from .retirement_models import (
    C2PInformation,
    CareerPeriod,
    EmployeeCareer,
    EvidenceGrade,
    EvidenceItem,
    ExposurePeriod,
    FiveShiftPeriod,
    MissingInformation,
    NightWorkPeriod,
    RetirementConfidence,
    RetirementOutputLevel,
    RetirementReport,
    RetirementScenario,
)
from .retirement_platform import RetirementArchitectureOnlyError, RetirementPlatform
from .retirement_reasoning_protocol import REASONING_PROTOCOL, ReasoningStep, RetirementReasoningStep
from .retirement_source_policy import RETIREMENT_SOURCE_POLICY, RetirementSourcePolicy, SourceAuthority

__all__ = (
    "C2PInformation",
    "CareerPeriod",
    "EVIDENCE_MATRIX",
    "EVIDENCE_WEIGHTING_RULES",
    "EmployeeCareer",
    "EvidenceGrade",
    "EvidenceItem",
    "EvidenceRequirement",
    "ExposurePeriod",
    "FiveShiftPeriod",
    "MissingInformation",
    "NightWorkPeriod",
    "REASONING_PROTOCOL",
    "RETIREMENT_FOUNDATION_CONTRACT",
    "RETIREMENT_SOURCE_POLICY",
    "ReasoningStep",
    "RetirementArchitectureOnlyError",
    "RetirementAssessmentPort",
    "RetirementConfidence",
    "RetirementFoundationContract",
    "RetirementOutputLevel",
    "RetirementPlatform",
    "RetirementQuestion",
    "RetirementReasoningStep",
    "RetirementReport",
    "RetirementRequest",
    "RetirementResponse",
    "RetirementScenario",
    "RetirementSourcePolicy",
    "SourceAuthority",
)
