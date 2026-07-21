"""Offline facade for synthetic payslip metadata."""

from __future__ import annotations

from .career_reconstruction_engine import CareerReconstructionEngine
from .career_reconstruction_models import ReconstructionRequest
from .payslip_converter import PayslipConverter
from .payslip_models import (
    Payslip,
    PayslipConfidence,
    PayslipEmployee,
    PayslipHeader,
    PayslipImport,
    PayslipMetadata,
    PayslipPayrollInformation,
    PayslipReport,
    PayslipReportView,
    PayslipStatus,
    PayslipValidation,
)
from .payslip_report import PayslipReportBuilder
from .payslip_validator import PayslipValidator


class PayslipConnector:
    """Prepare injected payroll metadata without parsers, APIs or I/O."""

    def __init__(self, validator=None, converter=None, report_builder=None, reconstruction_engine=None):
        self._validator = validator or PayslipValidator()
        self._converter = converter or PayslipConverter()
        self._report_builder = report_builder or PayslipReportBuilder()
        self._reconstruction_engine = reconstruction_engine or CareerReconstructionEngine()

    def create_empty_payslip(self, payslip_id: str, imported_at: str = "1970-01-01") -> Payslip:
        metadata = PayslipMetadata(
            payslip_id,
            f"synthetic:{payslip_id}",
            imported_at,
            "v1",
            PayslipConfidence.UNKNOWN,
            True,
        )
        return Payslip(metadata, PayslipHeader(), PayslipEmployee(f"synthetic-employee:{payslip_id}"), status=PayslipStatus.EMPTY)

    def validate_payslip(self, payslip: Payslip) -> PayslipValidation:
        return self._validator.validate(payslip)

    def convert_to_import_batch(self, payslip: Payslip):
        validation = self.validate_payslip(payslip)
        if not validation.valid:
            raise ValueError("Payslip must pass structural validation before conversion.")
        return self._converter.convert(payslip).import_batch

    def extract_payroll_information(self, payslip: Payslip) -> PayslipPayrollInformation:
        return PayslipPayrollInformation(
            tuple(item.period_id for item in payslip.periods),
            tuple(item.label for item in payslip.classifications if item.label),
            tuple(item.value for item in payslip.coefficients if item.value),
            tuple(item.schedule_label for item in payslip.working_times + payslip.five_shift if item.schedule_label),
            tuple(item.night_work_id for item in payslip.night_work),
            tuple(item.five_shift_id for item in payslip.five_shift),
            tuple(item.code for item in payslip.salary_items if item.code),
            tuple(item.code for item in payslip.contributions if item.code),
            tuple(item.absence_type for item in payslip.absences if item.absence_type),
            tuple(item.overtime_id for item in payslip.overtime),
        )

    def prepare_reconstruction(self, payslip: Payslip) -> PayslipImport:
        validation = self.validate_payslip(payslip)
        if not validation.valid:
            raise ValueError("Invalid payslip cannot prepare reconstruction.")
        converted = self._converter.convert(payslip)
        context = self._reconstruction_engine.create_reconstruction_context(
            f"payslip-context:{payslip.metadata.payslip_id}",
            ReconstructionRequest(
                f"payslip-request:{payslip.metadata.payslip_id}",
                "Prepare a synthetic payslip reconstruction proposal.",
            ),
        )
        context = self._reconstruction_engine.add_import_batch(context, converted.import_batch)
        proposal = self._reconstruction_engine.build_reconstruction_proposal(context)
        return PayslipImport(converted.payslip_id, converted.import_batch, converted.converted_record_ids, proposal)

    def generate_import_report(self, payslip: Payslip, view: PayslipReportView) -> PayslipReport:
        validation = self.validate_payslip(payslip)
        payroll = self.extract_payroll_information(payslip)
        converted = self._converter.convert(payslip)
        return self._report_builder.build(payslip, validation, payroll, converted, view)
