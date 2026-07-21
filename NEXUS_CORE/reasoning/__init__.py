"""Public API for the domain-neutral Nexus Core reasoning pipeline."""

from .confidence import ConfidenceEngine
from .conflicts import ConflictEngine
from .contracts import FactProducer, ReasoningEngine, ReasoningReporter
from .correlation import FactCorrelationEngine
from .corroboration import CorroborationEngine
from .facts import FactExtractor
from .missing_evidence import MissingEvidenceEngine
from .models import (
    ConfidenceAssessment,
    ConflictExplanation,
    Corroboration,
    CorroborationStrength,
    Fact,
    FactCollection,
    FactCorrelation,
    FactType,
    MissingEvidence,
    MissingEvidenceReason,
    ReasoningConfidence,
    ReasoningConflict,
    ReasoningReport,
    ReasoningStep,
)
from .pipeline import GenericReasoningPipeline
from .report import JsonReasoningReporter, ReasoningReportBuilder

__all__ = [
    "ConfidenceAssessment",
    "ConfidenceEngine",
    "ConflictEngine",
    "ConflictExplanation",
    "Corroboration",
    "CorroborationEngine",
    "CorroborationStrength",
    "Fact",
    "FactCollection",
    "FactCorrelation",
    "FactCorrelationEngine",
    "FactExtractor",
    "FactProducer",
    "FactType",
    "GenericReasoningPipeline",
    "JsonReasoningReporter",
    "MissingEvidence",
    "MissingEvidenceEngine",
    "MissingEvidenceReason",
    "ReasoningConfidence",
    "ReasoningConflict",
    "ReasoningEngine",
    "ReasoningReport",
    "ReasoningReportBuilder",
    "ReasoningReporter",
    "ReasoningStep",
]
