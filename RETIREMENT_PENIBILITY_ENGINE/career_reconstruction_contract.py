"""Public architecture-only contract for the Career Reconstruction Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .career_evidence_models import EvidenceBundle
from .career_import_models import ImportBatch
from .career_reconstruction_engine import CareerReconstructionEngine
from .career_reconstruction_models import (
    ReconstructionCandidate,
    ReconstructionConflict,
    ReconstructionContext,
    ReconstructionGap,
    ReconstructionMatch,
    ReconstructionMerge,
    ReconstructionProposal,
    ReconstructionReport,
    ReconstructionReportView,
    ReconstructionRequest,
    ReconstructedCareerEvent,
)


@dataclass(frozen=True)
class CareerReconstructionSafetyContract:
    """Safety declaration prohibiting I/O, calculations and auto-validation."""

    status: str = "ARCHITECTURE_ONLY"
    enabled: bool = False
    network_allowed: bool = False
    file_reading_allowed: bool = False
    pdf_parsing_allowed: bool = False
    ocr_allowed: bool = False
    api_allowed: bool = False
    artificial_intelligence_allowed: bool = False
    retirement_calculation_allowed: bool = False
    c2p_calculation_allowed: bool = False
    automatic_validation_allowed: bool = False


CAREER_RECONSTRUCTION_SAFETY_CONTRACT = CareerReconstructionSafetyContract()


class CareerReconstructionPort(Protocol):
    """Stable public methods implemented by CareerReconstructionEngine."""

    def create_reconstruction_context(
        self, context_id: str, request: ReconstructionRequest, existing_timeline=None, existing_evidence=None
    ) -> ReconstructionContext: ...

    def add_import_batch(self, context: ReconstructionContext, batch: ImportBatch) -> ReconstructionContext: ...

    def build_candidates(self, context: ReconstructionContext) -> tuple[ReconstructionCandidate, ...]: ...

    def match_records(self, context: ReconstructionContext) -> tuple[ReconstructionMatch, ...]: ...

    def merge_compatible_records(self, context: ReconstructionContext) -> tuple[ReconstructionMerge, ...]: ...

    def detect_conflicts(self, context: ReconstructionContext) -> tuple[ReconstructionConflict, ...]: ...

    def detect_gaps(self, context: ReconstructionContext) -> tuple[ReconstructionGap, ...]: ...

    def build_reconstruction_proposal(self, context: ReconstructionContext) -> ReconstructionProposal: ...

    def prepare_timeline_proposal(self, context: ReconstructionContext) -> tuple[ReconstructedCareerEvent, ...]: ...

    def prepare_evidence_proposal(self, context: ReconstructionContext) -> EvidenceBundle: ...

    def generate_reconstruction_report(
        self, context: ReconstructionContext, proposal: ReconstructionProposal, view: ReconstructionReportView
    ) -> ReconstructionReport: ...


__all__ = (
    "CareerReconstructionEngine",
    "CareerReconstructionPort",
    "CAREER_RECONSTRUCTION_SAFETY_CONTRACT",
)
