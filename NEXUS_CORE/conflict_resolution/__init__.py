"""Public API for the generic Nexus documentary resolution engine."""

from .classification import ResolutionClassifier
from .coherence import CoherenceEvaluator
from .contracts import ConflictResolutionEngine, ResolutionReporter
from .models import (
    CoherenceAssessment,
    ResolutionCandidate,
    ResolutionCategory,
    ResolutionClassification,
    ResolutionDiagnostic,
    ResolutionReport,
    ResolutionSummary,
)
from .pipeline import GenericConflictResolutionEngine
from .report import JsonResolutionReporter, ResolutionReportBuilder

__all__ = [
    "CoherenceAssessment",
    "CoherenceEvaluator",
    "ConflictResolutionEngine",
    "GenericConflictResolutionEngine",
    "JsonResolutionReporter",
    "ResolutionCandidate",
    "ResolutionCategory",
    "ResolutionClassification",
    "ResolutionClassifier",
    "ResolutionDiagnostic",
    "ResolutionReport",
    "ResolutionReportBuilder",
    "ResolutionReporter",
    "ResolutionSummary",
]
