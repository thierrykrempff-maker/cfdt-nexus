"""Public architecture-only contract for the Payslip Connector."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .career_import_models import ImportBatch
from .payslip_models import (
    Payslip,
    PayslipImport,
    PayslipPayrollInformation,
    PayslipReport,
    PayslipReportView,
    PayslipValidation,
)


@dataclass(frozen=True)
class PayslipSafetyContract:
    """Disable every real acquisition and sensitive-data capability."""

    status: str = "ARCHITECTURE_ONLY"
    enabled: bool = False
    network_allowed: bool = False
    file_reading_allowed: bool = False
    pdf_parsing_allowed: bool = False
    ocr_allowed: bool = False
    api_allowed: bool = False
    nibelis_access_allowed: bool = False
    kelio_access_allowed: bool = False
    real_payslips_allowed: bool = False
    personal_data_allowed: bool = False
    retirement_calculation_allowed: bool = False
    career_import_compatible: bool = True
    career_reconstruction_compatible: bool = True
    expert_paie_v2_compatible: bool = True
    nibelis_referential_compatible: bool = True
    kelio_referential_compatible: bool = True
    potential_rights_compatible: bool = True


PAYSLIP_SAFETY_CONTRACT = PayslipSafetyContract()


class PayslipPort(Protocol):
    """Stable public methods implemented by PayslipConnector."""

    def create_empty_payslip(self, payslip_id: str, imported_at: str = "1970-01-01") -> Payslip: ...

    def validate_payslip(self, payslip: Payslip) -> PayslipValidation: ...

    def convert_to_import_batch(self, payslip: Payslip) -> ImportBatch: ...

    def extract_payroll_information(self, payslip: Payslip) -> PayslipPayrollInformation: ...

    def prepare_reconstruction(self, payslip: Payslip) -> PayslipImport: ...

    def generate_import_report(self, payslip: Payslip, view: PayslipReportView) -> PayslipReport: ...


__all__ = ("PayslipPort", "PAYSLIP_SAFETY_CONTRACT")
