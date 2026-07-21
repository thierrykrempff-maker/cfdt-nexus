"""Offline facade for synthetic Kelio metadata."""

from __future__ import annotations

from .career_import_pipeline import CareerImportPipeline
from .connector_base import ConnectorFoundation, ConnectorReconstructionSpec
from .kelio_converter import KelioConverter
from .kelio_referential_adapter import PayrollKelioReferentialLookup
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

    _RECONSTRUCTION = ConnectorReconstructionSpec(
        "kelio-context",
        "kelio-request",
        "Prepare a synthetic Kelio reconstruction proposal.",
    )

    _DEFAULT_LOOKUP = object()

    def __init__(
        self,
        validator=None,
        converter=None,
        report_builder=None,
        import_pipeline=None,
        referential_lookup=_DEFAULT_LOOKUP,
    ):
        if referential_lookup is self._DEFAULT_LOOKUP:
            referential_lookup = PayrollKelioReferentialLookup()
        self._converter = converter or KelioConverter(referential_lookup)
        self._foundation = ConnectorFoundation(
            validator or KelioValidator(),
            self._converter,
            import_pipeline or CareerImportPipeline(),
        )
        self._report_builder = report_builder or KelioReportBuilder()

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
        return self._foundation.validate(export)

    def convert_to_import_batch(self, export: KelioExport):
        return self._foundation.convert_validated(
            export,
            "Kelio export must pass structural validation before conversion.",
        ).import_batch

    def extract_working_time(self, export: KelioExport) -> KelioWorkingTimeInformation:
        if not self.validate_export(export).valid:
            raise ValueError("Invalid Kelio export cannot resolve counters.")
        self._foundation.assert_safe(export)
        resolutions = self._converter.resolve_counters(export)
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
            resolutions,
        )

    def prepare_reconstruction(self, export: KelioExport) -> KelioImport:
        converted = self._foundation.convert_validated(
            export,
            "Invalid Kelio export cannot prepare reconstruction.",
        )
        proposal = self._foundation.prepare_reconstruction(
            export.metadata.export_id,
            converted.import_batch,
            self._RECONSTRUCTION,
        )
        return KelioImport(
            converted.export_id,
            converted.import_batch,
            converted.converted_record_ids,
            converted.counter_resolutions,
            proposal,
        )

    def generate_import_report(self, export: KelioExport, view: KelioReportView) -> KelioReport:
        validation = self.validate_export(export)
        information = self.extract_working_time(export)
        converted = self._foundation.convert(export)
        return self._report_builder.build(export, validation, information, converted, view)
