"""Offline facade connecting synthetic statements to existing career engines."""

from __future__ import annotations

from .career_reconstruction_engine import CareerReconstructionEngine
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
from .connector_base import ConnectorFoundation, ConnectorReconstructionSpec


class CareerStatementConnector:
    """Prepare injected metadata without parsing, network access or I/O."""

    _RECONSTRUCTION = ConnectorReconstructionSpec(
        "statement-context",
        "statement-request",
        "Prepare a synthetic career-statement reconstruction proposal.",
    )

    def __init__(self, validator=None, converter=None, report_builder=None, reconstruction_engine=None):
        self._foundation = ConnectorFoundation(
            validator or CareerStatementValidator(),
            converter or CareerStatementConverter(),
            reconstruction_engine or CareerReconstructionEngine(),
        )
        self._report_builder = report_builder or CareerStatementReportBuilder()

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
        return self._foundation.validate(statement)

    def convert_to_import_batch(self, statement: CareerStatement):
        return self._foundation.convert_validated(
            statement,
            "Career statement must pass structural validation before conversion.",
        ).import_batch

    def generate_import_report(
        self, statement: CareerStatement, view: CareerStatementReportView
    ) -> CareerStatementReport:
        validation = self.validate_statement(statement)
        conversion = self._foundation.convert(statement)
        return self._report_builder.build(statement, validation, conversion, view)

    def extract_metadata(self, statement: CareerStatement) -> CareerStatementMetadata:
        return statement.metadata

    def prepare_reconstruction(self, statement: CareerStatement) -> CareerStatementImport:
        conversion = self._foundation.convert_validated(
            statement,
            "Invalid career statement cannot prepare reconstruction.",
        )
        proposal = self._foundation.prepare_reconstruction(
            statement.metadata.statement_id,
            conversion.import_batch,
            self._RECONSTRUCTION,
        )
        return CareerStatementImport(statement.metadata.statement_id, conversion, proposal)
