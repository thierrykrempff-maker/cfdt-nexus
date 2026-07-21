"""Public architecture-only contract for Employment Contract Connector."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .career_import_models import ImportBatch
from .employment_contract_connector import EmploymentContractConnector
from .employment_contract_models import (
    EmploymentContract,
    EmploymentContractInformation,
    EmploymentImport,
    EmploymentReport,
    EmploymentReportView,
    EmploymentValidation,
)


@dataclass(frozen=True)
class EmploymentContractSafetyContract:
    """Disable real document access, sensitive data and decisions."""

    status: str = "ARCHITECTURE_ONLY"
    enabled: bool = False
    network_allowed: bool = False
    file_reading_allowed: bool = False
    pdf_parsing_allowed: bool = False
    ocr_allowed: bool = False
    api_allowed: bool = False
    real_documents_allowed: bool = False
    personal_data_allowed: bool = False
    legal_validation_allowed: bool = False
    calculation_allowed: bool = False
    career_statement_compatible: bool = True
    payslip_compatible: bool = True
    career_import_compatible: bool = True
    career_reconstruction_compatible: bool = True
    career_timeline_compatible: bool = True
    career_evidence_compatible: bool = True
    potential_rights_compatible: bool = True


EMPLOYMENT_CONTRACT_SAFETY_CONTRACT = EmploymentContractSafetyContract()


class EmploymentContractPort(Protocol):
    """Stable public methods implemented by EmploymentContractConnector."""

    def create_empty_contract(self, contract_id: str, imported_at: str = "1970-01-01") -> EmploymentContract: ...

    def validate_contract(self, contract: EmploymentContract) -> EmploymentValidation: ...

    def convert_to_import_batch(self, contract: EmploymentContract) -> ImportBatch: ...

    def extract_contract_information(self, contract: EmploymentContract) -> EmploymentContractInformation: ...

    def prepare_reconstruction(self, contract: EmploymentContract) -> EmploymentImport: ...

    def generate_import_report(self, contract: EmploymentContract, view: EmploymentReportView) -> EmploymentReport: ...


__all__ = (
    "EmploymentContractConnector",
    "EmploymentContractPort",
    "EMPLOYMENT_CONTRACT_SAFETY_CONTRACT",
)
