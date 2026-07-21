"""Audience-safe reporting for structural career-import preparation."""

from __future__ import annotations

import re

from .career_import_models import (
    ImportBatch,
    ImportConflict,
    ImportNormalization,
    ImportRecommendation,
    ImportReport,
    ImportReportView,
    ImportSummary,
    ImportValidation,
)


_FORBIDDEN_MARKERS = ("secret", "token", "password", "diagnosis", "medical detail", "nir")


def _safe(value: str) -> str:
    lowered = value.lower()
    if any(marker in lowered for marker in _FORBIDDEN_MARKERS):
        return "[REDACTED]"
    if re.search(r"(?:^|\s)[a-zA-Z]:[\\/]", value) or value.startswith(("/", "\\\\")):
        return "[REDACTED]"
    return value


class CareerImportReportBuilder:
    """Build employee and expert views without document content or local paths."""

    def build(
        self,
        batch: ImportBatch,
        summary: ImportSummary,
        validation: ImportValidation,
        normalizations: tuple[ImportNormalization, ...],
        conflicts: tuple[ImportConflict, ...],
        recommendations: tuple[ImportRecommendation, ...],
        view: ImportReportView,
    ) -> ImportReport:
        documents = tuple(_safe(item.title) for item in batch.documents)
        missing = tuple(
            "Document metadata is incomplete."
            for item in batch.documents
            if not item.complete
        )
        inconsistencies = tuple(_safe(item.description) for item in validation.issues) + tuple(
            _safe(item.description) for item in conflicts
        )
        next_steps = tuple(_safe(item.action) for item in recommendations)
        warnings = (
            "No source document was opened, parsed or copied.",
            "Prepared records require human review before use.",
        )
        if view is ImportReportView.EMPLOYEE_VIEW:
            return ImportReport(
                view, summary, documents, missing, inconsistencies, next_steps, warnings
            )
        provenance = tuple(
            _safe(
                f"{record.provenance.document_type.value}: "
                f"{record.provenance.internal_document_id} / {record.provenance.version} / "
                f"{record.provenance.origin}"
            )
            for record in batch.records
        )
        normalization_details = tuple(
            _safe(f"{item.record_id}: {', '.join(item.transformations) or 'no transformation'}")
            for item in normalizations
        )
        return ImportReport(
            view,
            summary,
            documents,
            missing,
            inconsistencies,
            next_steps,
            warnings,
            provenance=provenance,
            normalizations=normalization_details,
            conflicts=tuple(_safe(item.description) for item in conflicts),
            validations=tuple(_safe(item.description) for item in validation.issues),
            recommendations=next_steps,
        )
