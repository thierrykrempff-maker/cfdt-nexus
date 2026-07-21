"""Public architecture-only contract for the Kelio Connector."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .career_import_models import ImportBatch
from .kelio_connector import KelioConnector
from .kelio_models import (
    KelioExport,
    KelioImport,
    KelioReport,
    KelioReportView,
    KelioValidation,
    KelioWorkingTimeInformation,
)


@dataclass(frozen=True)
class KelioSafetyContract:
    """Disable real export access, identifiers, APIs and calculations."""

    status: str = "ARCHITECTURE_ONLY"
    enabled: bool = False
    network_allowed: bool = False
    file_reading_allowed: bool = False
    export_parsing_allowed: bool = False
    ocr_allowed: bool = False
    api_allowed: bool = False
    kelio_access_allowed: bool = False
    real_exports_allowed: bool = False
    personal_data_allowed: bool = False
    calculation_allowed: bool = False
    career_statement_compatible: bool = True
    payslip_compatible: bool = True
    employment_contract_compatible: bool = True
    career_import_compatible: bool = True
    career_reconstruction_compatible: bool = True
    career_timeline_compatible: bool = True
    career_evidence_compatible: bool = True
    potential_rights_compatible: bool = True
    kelio_referential_compatible: bool = True


KELIO_SAFETY_CONTRACT = KelioSafetyContract()


class KelioPort(Protocol):
    """Stable public methods implemented by KelioConnector."""

    def create_empty_export(self, export_id: str, imported_at: str = "1970-01-01") -> KelioExport: ...

    def validate_export(self, export: KelioExport) -> KelioValidation: ...

    def convert_to_import_batch(self, export: KelioExport) -> ImportBatch: ...

    def extract_working_time(self, export: KelioExport) -> KelioWorkingTimeInformation: ...

    def prepare_reconstruction(self, export: KelioExport) -> KelioImport: ...

    def generate_import_report(self, export: KelioExport, view: KelioReportView) -> KelioReport: ...


__all__ = ("KelioConnector", "KelioPort", "KELIO_SAFETY_CONTRACT")
