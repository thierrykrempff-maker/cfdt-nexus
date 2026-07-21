"""Offline facade for synthetic Nibelis metadata."""

from __future__ import annotations

from dataclasses import dataclass

from .career_reconstruction_engine import CareerReconstructionEngine
from .career_reconstruction_models import ReconstructionRequest
from .nibelis_converter import NibelisConverter
from .nibelis_models import (
    NibelisConfidence,
    NibelisExport,
    NibelisImport,
    NibelisMetadata,
    NibelisPayrollInformation,
    NibelisReport,
    NibelisReportView,
    NibelisStatus,
    NibelisValidation,
)
from .nibelis_report import NibelisReportBuilder
from .nibelis_validator import NibelisValidator


@dataclass(frozen=True)
class InjectedNibelisReferentialLookup:
    """Identifier projection injected from existing validated referentials."""

    rubric_ids: frozenset[str]
    parameter_ids: frozenset[str] = frozenset()

    def contains_rubric(self, rubric_id: str) -> bool:
        return rubric_id in self.rubric_ids

    def contains_parameter(self, parameter_id: str) -> bool:
        return parameter_id in self.parameter_ids


class NibelisConnector:
    """Prepare injected occurrences without Nibelis access, files or APIs."""

    def __init__(self, referential_lookup=None, validator=None, converter=None, report_builder=None, reconstruction_engine=None):
        self._validator = validator or NibelisValidator(referential_lookup)
        self._converter = converter or NibelisConverter()
        self._report_builder = report_builder or NibelisReportBuilder()
        self._reconstruction_engine = reconstruction_engine or CareerReconstructionEngine()

    def create_empty_export(self, export_id: str, imported_at: str = "1970-01-01") -> NibelisExport:
        metadata = NibelisMetadata(
            export_id,
            f"synthetic:{export_id}",
            imported_at,
            "v1",
            NibelisConfidence.UNKNOWN,
            True,
        )
        return NibelisExport(metadata, status=NibelisStatus.EMPTY)

    def validate_export(self, export: NibelisExport) -> NibelisValidation:
        return self._validator.validate(export)

    def extract_payroll_data(self, export: NibelisExport) -> NibelisPayrollInformation:
        rubric_ids = tuple(
            dict.fromkeys(
                item.referential_rubric_id
                for item in export.salary_items + export.contributions
            )
        )
        return NibelisPayrollInformation(
            tuple(item.period_id for item in export.periods),
            rubric_ids,
            tuple(item.item_id for item in export.salary_items),
            tuple(item.contribution_id for item in export.contributions),
            tuple(item.referential_parameter_id for item in export.parameters),
            tuple(item.label for item in export.classifications if item.label),
            tuple(item.value for item in export.coefficients if item.value),
        )

    def convert_to_import_batch(self, export: NibelisExport):
        validation = self.validate_export(export)
        if not validation.valid:
            raise ValueError("Nibelis export must pass structural validation before conversion.")
        return self._converter.convert(export).import_batch

    def prepare_reconstruction(self, export: NibelisExport) -> NibelisImport:
        validation = self.validate_export(export)
        if not validation.valid:
            raise ValueError("Invalid Nibelis export cannot prepare reconstruction.")
        converted = self._converter.convert(export)
        context = self._reconstruction_engine.create_reconstruction_context(
            f"nibelis-context:{export.metadata.export_id}",
            ReconstructionRequest(
                f"nibelis-request:{export.metadata.export_id}",
                "Prepare a synthetic Nibelis reconstruction proposal.",
            ),
        )
        context = self._reconstruction_engine.add_import_batch(context, converted.import_batch)
        proposal = self._reconstruction_engine.build_reconstruction_proposal(context)
        return NibelisImport(converted.export_id, converted.import_batch, converted.converted_record_ids, proposal)

    def generate_import_report(self, export: NibelisExport, view: NibelisReportView) -> NibelisReport:
        validation = self.validate_export(export)
        information = self.extract_payroll_data(export)
        converted = self._converter.convert(export)
        return self._report_builder.build(export, validation, information, converted, view)
