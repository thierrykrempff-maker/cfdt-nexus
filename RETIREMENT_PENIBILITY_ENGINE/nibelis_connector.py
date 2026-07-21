"""Offline facade for synthetic Nibelis metadata."""

from __future__ import annotations

from dataclasses import dataclass

from .career_reconstruction_engine import CareerReconstructionEngine
from .connector_base import ConnectorFoundation, ConnectorReconstructionSpec
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

    _RECONSTRUCTION = ConnectorReconstructionSpec(
        "nibelis-context",
        "nibelis-request",
        "Prepare a synthetic Nibelis reconstruction proposal.",
    )

    def __init__(self, referential_lookup=None, validator=None, converter=None, report_builder=None, reconstruction_engine=None):
        self._foundation = ConnectorFoundation(
            validator or NibelisValidator(referential_lookup),
            converter or NibelisConverter(),
            reconstruction_engine or CareerReconstructionEngine(),
        )
        self._report_builder = report_builder or NibelisReportBuilder()

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
        return self._foundation.validate(export)

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
        return self._foundation.convert_validated(
            export,
            "Nibelis export must pass structural validation before conversion.",
        ).import_batch

    def prepare_reconstruction(self, export: NibelisExport) -> NibelisImport:
        converted = self._foundation.convert_validated(
            export,
            "Invalid Nibelis export cannot prepare reconstruction.",
        )
        proposal = self._foundation.prepare_reconstruction(
            export.metadata.export_id,
            converted.import_batch,
            self._RECONSTRUCTION,
        )
        return NibelisImport(converted.export_id, converted.import_batch, converted.converted_record_ids, proposal)

    def generate_import_report(self, export: NibelisExport, view: NibelisReportView) -> NibelisReport:
        validation = self.validate_export(export)
        information = self.extract_payroll_data(export)
        converted = self._foundation.convert(export)
        return self._report_builder.build(export, validation, information, converted, view)
