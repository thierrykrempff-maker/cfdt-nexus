"""Public architecture-only contract for the Career Import Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .career_evidence_models import EvidenceBundle
from .career_import_models import (
    ImportBatch,
    ImportConflict,
    ImportNormalization,
    ImportReport,
    ImportReportView,
    ImportSummary,
    ImportValidation,
)
from .career_timeline_models import CareerTimeline


@dataclass(frozen=True)
class CareerImportSafetyContract:
    """Safety declaration prohibiting all real acquisition and parsing."""

    status: str = "ARCHITECTURE_ONLY"
    enabled: bool = False
    file_reading_allowed: bool = False
    pdf_parsing_allowed: bool = False
    payroll_parsing_allowed: bool = False
    kelio_parsing_allowed: bool = False
    nibelis_parsing_allowed: bool = False
    ocr_allowed: bool = False
    api_allowed: bool = False
    network_allowed: bool = False
    automatic_reconstruction_allowed: bool = False


CAREER_IMPORT_SAFETY_CONTRACT = CareerImportSafetyContract()


class CareerImportPort(Protocol):
    """Stable public methods implemented by CareerImportEngine."""

    def create_import_batch(self, batch_id: str, documents=(), records=()) -> ImportBatch: ...

    def validate_batch(self, batch: ImportBatch) -> ImportValidation: ...

    def normalize_batch(self, batch: ImportBatch) -> tuple[ImportNormalization, ...]: ...

    def detect_conflicts(self, batch: ImportBatch) -> tuple[ImportConflict, ...]: ...

    def build_import_summary(
        self, batch, validation, normalizations, conflicts
    ) -> ImportSummary: ...

    def generate_report(
        self, batch, validation, normalizations, conflicts, view: ImportReportView
    ) -> ImportReport: ...

    def prepare_timeline_records(
        self, batch: ImportBatch, normalizations: tuple[ImportNormalization, ...]
    ) -> CareerTimeline: ...

    def prepare_evidence_records(self, batch: ImportBatch) -> EvidenceBundle: ...


__all__ = (
    "CareerImportPort",
    "CAREER_IMPORT_SAFETY_CONTRACT",
)
