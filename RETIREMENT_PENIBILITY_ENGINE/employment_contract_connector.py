"""Offline facade for synthetic employment-contract metadata."""

from __future__ import annotations

from .career_reconstruction_engine import CareerReconstructionEngine
from .career_reconstruction_models import ReconstructionRequest
from .employment_contract_converter import EmploymentContractConverter
from .employment_contract_models import (
    EmploymentConfidence,
    EmploymentContract,
    EmploymentContractInformation,
    EmploymentImport,
    EmploymentMetadata,
    EmploymentReport,
    EmploymentReportView,
    EmploymentStatus,
    EmploymentValidation,
)
from .employment_contract_report import EmploymentContractReportBuilder
from .employment_contract_validator import EmploymentContractValidator


class EmploymentContractConnector:
    """Prepare injected contract metadata without parsers, APIs or I/O."""

    def __init__(self, validator=None, converter=None, report_builder=None, reconstruction_engine=None):
        self._validator = validator or EmploymentContractValidator()
        self._converter = converter or EmploymentContractConverter()
        self._report_builder = report_builder or EmploymentContractReportBuilder()
        self._reconstruction_engine = reconstruction_engine or CareerReconstructionEngine()

    def create_empty_contract(self, contract_id: str, imported_at: str = "1970-01-01") -> EmploymentContract:
        metadata = EmploymentMetadata(
            contract_id,
            f"synthetic:{contract_id}",
            imported_at,
            "v1",
            EmploymentConfidence.UNKNOWN,
            True,
        )
        return EmploymentContract(metadata, status=EmploymentStatus.EMPTY)

    def validate_contract(self, contract: EmploymentContract) -> EmploymentValidation:
        return self._validator.validate(contract)

    def convert_to_import_batch(self, contract: EmploymentContract):
        validation = self.validate_contract(contract)
        if not validation.valid:
            raise ValueError("Employment contract must pass structural validation before conversion.")
        return self._converter.convert(contract).import_batch

    def extract_contract_information(self, contract: EmploymentContract) -> EmploymentContractInformation:
        return EmploymentContractInformation(
            contract.metadata.contract_id,
            tuple(item.period_id for item in contract.periods),
            tuple(item.amendment_id for item in contract.amendments),
            tuple(item.label for item in contract.positions if item.label),
            tuple(item.label for item in contract.classifications if item.label),
            tuple(item.value for item in contract.coefficients if item.value),
            tuple(item.label for item in contract.schedules if item.label),
            tuple(item.declared_hours for item in contract.working_times if item.declared_hours),
            tuple(item.five_shift_id for item in contract.five_shift),
            tuple(item.night_work_id for item in contract.night_work),
        )

    def prepare_reconstruction(self, contract: EmploymentContract) -> EmploymentImport:
        validation = self.validate_contract(contract)
        if not validation.valid:
            raise ValueError("Invalid employment contract cannot prepare reconstruction.")
        converted = self._converter.convert(contract)
        context = self._reconstruction_engine.create_reconstruction_context(
            f"employment-contract-context:{contract.metadata.contract_id}",
            ReconstructionRequest(
                f"employment-contract-request:{contract.metadata.contract_id}",
                "Prepare a synthetic employment-contract reconstruction proposal.",
            ),
        )
        context = self._reconstruction_engine.add_import_batch(context, converted.import_batch)
        proposal = self._reconstruction_engine.build_reconstruction_proposal(context)
        return EmploymentImport(converted.contract_id, converted.import_batch, converted.converted_record_ids, proposal)

    def generate_import_report(self, contract: EmploymentContract, view: EmploymentReportView) -> EmploymentReport:
        validation = self.validate_contract(contract)
        information = self.extract_contract_information(contract)
        converted = self._converter.convert(contract)
        return self._report_builder.build(contract, validation, information, converted, view)
