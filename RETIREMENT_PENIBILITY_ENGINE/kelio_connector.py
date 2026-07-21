"""Offline facade for synthetic Kelio metadata."""

from __future__ import annotations

from .career_reconstruction_engine import CareerReconstructionEngine
from .career_reconstruction_models import ReconstructionRequest
from .kelio_converter import KelioConverter
from .kelio_models import (
    KelioConfidence,
    KelioEmployee,
    KelioExport,
    KelioImport,
    KelioMetadata,
    KelioReport,
    KelioReportView,
    KelioStatus,
    KelioValidation,
    KelioWorkingTimeInformation,
)
from .kelio_report import KelioReportBuilder
from .kelio_validator import KelioValidator


class KelioConnector:
    """Prepare injected Kelio metadata without file access, API or parsing."""

    def __init__(self, validator=None, converter=None, report_builder=None, reconstruction_engine=None):
        self._validator = validator or KelioValidator()
        self._converter = converter or KelioConverter()
        self._report_builder = report_builder or KelioReportBuilder()
        self._reconstruction_engine = reconstruction_engine or CareerReconstructionEngine()

    def create_empty_export(self, export_id: str, imported_at: str = "1970-01-01") -> KelioExport:
        metadata = KelioMetadata(
            export_id,
            f"synthetic:{export_id}",
            imported_at,
            "v1",
            KelioConfidence.UNKNOWN,
            True,
        )
        return KelioExport(metadata, KelioEmployee(f"synthetic-employee:{export_id}"), status=KelioStatus.EMPTY)

    def validate_export(self, export: KelioExport) -> KelioValidation:
        return self._validator.validate(export)

    def convert_to_import_batch(self, export: KelioExport):
        validation = self.validate_export(export)
        if not validation.valid:
            raise ValueError("Kelio export must pass structural validation before conversion.")
        return self._converter.convert(export).import_batch

    def extract_working_time(self, export: KelioExport) -> KelioWorkingTimeInformation:
        return KelioWorkingTimeInformation(
            tuple(item.working_time_id for item in export.working_times),
            tuple(item.label for item in export.schedules if item.label),
            tuple(item.night_work_id for item in export.night_work),
            tuple(item.five_shift_id for item in export.five_shift),
            tuple(item.on_call_id for item in export.on_calls),
            tuple(item.intervention_id for item in export.interventions),
            tuple(item.leave_id for item in export.leaves),
            tuple(
                f"{item.label}:{item.declared_value}"
                for item in export.counters
                if item.label and item.declared_value is not None
            ),
        )

    def prepare_reconstruction(self, export: KelioExport) -> KelioImport:
        validation = self.validate_export(export)
        if not validation.valid:
            raise ValueError("Invalid Kelio export cannot prepare reconstruction.")
        converted = self._converter.convert(export)
        context = self._reconstruction_engine.create_reconstruction_context(
            f"kelio-context:{export.metadata.export_id}",
            ReconstructionRequest(
                f"kelio-request:{export.metadata.export_id}",
                "Prepare a synthetic Kelio reconstruction proposal.",
            ),
        )
        context = self._reconstruction_engine.add_import_batch(context, converted.import_batch)
        proposal = self._reconstruction_engine.build_reconstruction_proposal(context)
        return KelioImport(converted.export_id, converted.import_batch, converted.converted_record_ids, proposal)

    def generate_import_report(self, export: KelioExport, view: KelioReportView) -> KelioReport:
        validation = self.validate_export(export)
        information = self.extract_working_time(export)
        converted = self._converter.convert(export)
        return self._report_builder.build(export, validation, information, converted, view)
