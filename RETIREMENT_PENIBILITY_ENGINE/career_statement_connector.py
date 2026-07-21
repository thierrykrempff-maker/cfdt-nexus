"""Offline facade connecting synthetic statements to existing career engines."""

from __future__ import annotations

from .career_reconstruction_engine import CareerReconstructionEngine
from .career_reconstruction_models import ReconstructionRequest
from .career_statement_converter import CareerStatementConverter
from .career_statement_models import (
    CareerStatement,
    CareerStatementConfidence,
    CareerStatementHeader,
    CareerStatementImport,
    CareerStatementMetadata,
    CareerStatementReport,
    CareerStatementReportView,
    CareerStatementSource,
    CareerStatementStatus,
    CareerStatementValidation,
)
from .career_statement_report import CareerStatementReportBuilder
from .career_statement_validator import CareerStatementValidator


class CareerStatementConnector:
    """Prepare injected metadata without parsing, network access or I/O."""

    def __init__(self, validator=None, converter=None, report_builder=None, reconstruction_engine=None):
        self._validator = validator or CareerStatementValidator()
        self._converter = converter or CareerStatementConverter()
        self._report_builder = report_builder or CareerStatementReportBuilder()
        self._reconstruction_engine = reconstruction_engine or CareerReconstructionEngine()

    def create_empty_statement(
        self,
        statement_id: str,
        imported_at: str = "1970-01-01",
        source: CareerStatementSource = CareerStatementSource.SYNTHETIC_TEST,
    ) -> CareerStatement:
        metadata = CareerStatementMetadata(
            statement_id,
            source,
            f"synthetic:{statement_id}",
            None,
            imported_at,
            "v1",
            CareerStatementConfidence.UNKNOWN,
            True,
        )
        return CareerStatement(metadata, CareerStatementHeader(), status=CareerStatementStatus.EMPTY)

    def validate_statement(self, statement: CareerStatement) -> CareerStatementValidation:
        return self._validator.validate(statement)

    def convert_to_import_batch(self, statement: CareerStatement):
        validation = self.validate_statement(statement)
        if not validation.valid:
            raise ValueError("Career statement must pass structural validation before conversion.")
        return self._converter.convert(statement).import_batch

    def generate_import_report(
        self, statement: CareerStatement, view: CareerStatementReportView
    ) -> CareerStatementReport:
        validation = self.validate_statement(statement)
        conversion = self._converter.convert(statement)
        return self._report_builder.build(statement, validation, conversion, view)

    def extract_metadata(self, statement: CareerStatement) -> CareerStatementMetadata:
        return statement.metadata

    def prepare_reconstruction(self, statement: CareerStatement) -> CareerStatementImport:
        validation = self.validate_statement(statement)
        if not validation.valid:
            raise ValueError("Invalid career statement cannot prepare reconstruction.")
        conversion = self._converter.convert(statement)
        context = self._reconstruction_engine.create_reconstruction_context(
            f"statement-context:{statement.metadata.statement_id}",
            ReconstructionRequest(
                f"statement-request:{statement.metadata.statement_id}",
                "Prepare a synthetic career-statement reconstruction proposal.",
            ),
        )
        context = self._reconstruction_engine.add_import_batch(context, conversion.import_batch)
        proposal = self._reconstruction_engine.build_reconstruction_proposal(context)
        return CareerStatementImport(statement.metadata.statement_id, conversion, proposal)
