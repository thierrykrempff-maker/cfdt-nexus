"""Public API for the CFDT Nexus Final Assistant."""

from .actions import ActionGenerator
from .contradictions import ContradictionResolver
from .critic import FinalCritic
from .engine import NexusFinalAssistant
from .models import (
    ActionDraft,
    AnalysisPlan,
    AssistantRequest,
    Confidence,
    CriticResult,
    Domain,
    DomainMatch,
    Fact,
    FinalAssistantResponse,
    FusedQuestion,
    NormalizedEngineResult,
    PrivacyDecision,
    QuestionPriority,
    ResponseMode,
    SourceItem,
    TechnicalTrace,
)
from .planning import AnalysisPlanner
from .privacy import PrivacyAssessment, PrivacyGate
from .routing import DomainDetector
from .synthesis import SynthesisEngine

__all__ = [
    "ActionDraft",
    "ActionGenerator",
    "AnalysisPlan",
    "AnalysisPlanner",
    "AssistantRequest",
    "Confidence",
    "ContradictionResolver",
    "CriticResult",
    "Domain",
    "DomainDetector",
    "DomainMatch",
    "Fact",
    "FinalAssistantResponse",
    "FinalCritic",
    "FusedQuestion",
    "NexusFinalAssistant",
    "NormalizedEngineResult",
    "PrivacyAssessment",
    "PrivacyDecision",
    "PrivacyGate",
    "QuestionPriority",
    "ResponseMode",
    "SourceItem",
    "SynthesisEngine",
    "TechnicalTrace",
]
