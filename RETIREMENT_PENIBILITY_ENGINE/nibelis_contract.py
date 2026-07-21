"""Public architecture-only contract for the Nibelis Connector."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .career_import_models import ImportBatch
from .nibelis_models import (
    NibelisExport,
    NibelisImport,
    NibelisPayrollInformation,
    NibelisReferentialLookup,
    NibelisReport,
    NibelisReportView,
    NibelisValidation,
)


@dataclass(frozen=True)
class NibelisReferentialCompatibility:
    """Stable locations and API used without loading files automatically."""

    referential_kind: str = "nibelis"
    schema_path: str = "database/payroll/referentials/nibelis-rubrics.schema.json"
    catalog_path: str = "database/payroll/referentials/nibelis-rubrics.example.json"
    validator_module: str = "automation.payroll.payroll_referential_validator"
    identifier_field: str = "rubric_id"
    parameter_referential_kind: str = "parameters"


NIBELIS_REFERENTIAL_COMPATIBILITY = NibelisReferentialCompatibility()


@dataclass(frozen=True)
class NibelisSafetyContract:
    status: str = "ARCHITECTURE_ONLY"
    enabled: bool = False
    network_allowed: bool = False
    file_reading_allowed: bool = False
    export_parsing_allowed: bool = False
    payslip_parsing_allowed: bool = False
    ocr_allowed: bool = False
    api_allowed: bool = False
    nibelis_access_allowed: bool = False
    real_documents_allowed: bool = False
    personal_or_bank_data_allowed: bool = False
    retirement_calculation_allowed: bool = False
    career_statement_compatible: bool = True
    payslip_compatible: bool = True
    employment_contract_compatible: bool = True
    kelio_compatible: bool = True
    career_import_compatible: bool = True
    career_reconstruction_compatible: bool = True
    potential_rights_compatible: bool = True
    existing_nibelis_referential_required: bool = True


NIBELIS_SAFETY_CONTRACT = NibelisSafetyContract()


class NibelisPort(Protocol):
    def create_empty_export(self, export_id: str, imported_at: str = "1970-01-01") -> NibelisExport: ...

    def validate_export(self, export: NibelisExport) -> NibelisValidation: ...

    def extract_payroll_data(self, export: NibelisExport) -> NibelisPayrollInformation: ...

    def convert_to_import_batch(self, export: NibelisExport) -> ImportBatch: ...

    def prepare_reconstruction(self, export: NibelisExport) -> NibelisImport: ...

    def generate_import_report(self, export: NibelisExport, view: NibelisReportView) -> NibelisReport: ...


__all__ = (
    "NibelisPort",
    "NibelisReferentialLookup",
    "NIBELIS_REFERENTIAL_COMPATIBILITY",
    "NIBELIS_SAFETY_CONTRACT",
)
