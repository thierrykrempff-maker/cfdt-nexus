"""Offline facade for synthetic employment-contract metadata."""

from __future__ import annotations

from .career_reconstruction_engine import CareerReconstructionEngine
from .connector_base import ConnectorFoundation, ConnectorReconstructionSpec
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

    _RECONSTRUCTION = ConnectorReconstructionSpec(
        "employment-contract-context",
        "employment-contract-request",
        "Prepare a synthetic employment-contract reconstruction proposal.",
    )

    def __init__(self, validator=None, converter=None, report_builder=None, reconstruction_engine=None):
        self._foundation = ConnectorFoundation(
            validator or EmploymentContractValidator(),
            converter or EmploymentContractConverter(),
            reconstruction_engine or CareerReconstructionEngine(),
        )
        self._report_builder = report_builder or EmploymentContractReportBuilder()

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
        return self._foundation.validate(contract)

    def convert_to_import_batch(self, contract: EmploymentContract):
        return self._foundation.convert_validated(
            contract,
            "Employment contract must pass structural validation before conversion.",
        ).import_batch

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
        converted = self._foundation.convert_validated(
            contract,
            "Invalid employment contract cannot prepare reconstruction.",
        )
        proposal = self._foundation.prepare_reconstruction(
            contract.metadata.contract_id,
            converted.import_batch,
            self._RECONSTRUCTION,
        )
        return EmploymentImport(converted.contract_id, converted.import_batch, converted.converted_record_ids, proposal)

    def generate_import_report(self, contract: EmploymentContract, view: EmploymentReportView) -> EmploymentReport:
        validation = self.validate_contract(contract)
        information = self.extract_contract_information(contract)
        converted = self._foundation.convert(contract)
        return self._report_builder.build(contract, validation, information, converted, view)
