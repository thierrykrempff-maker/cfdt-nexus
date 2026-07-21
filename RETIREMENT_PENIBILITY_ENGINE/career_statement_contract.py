"""Public architecture-only contract for the Career Statement Connector."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .career_import_models import ImportBatch
from .career_statement_models import (
    CareerStatement,
    CareerStatementImport,
    CareerStatementMetadata,
    CareerStatementReport,
    CareerStatementReportView,
    CareerStatementValidation,
)


@dataclass(frozen=True)
class CareerStatementSafetyContract:
    """Explicitly prohibit real acquisition, parsing and sensitive data."""

    status: str = "ARCHITECTURE_ONLY"
    enabled: bool = False
    network_allowed: bool = False
    carsat_api_allowed: bool = False
    cnav_api_allowed: bool = False
    france_connect_allowed: bool = False
    file_reading_allowed: bool = False
    pdf_parsing_allowed: bool = False
    ocr_allowed: bool = False
    scraping_allowed: bool = False
    real_documents_allowed: bool = False
    personal_data_allowed: bool = False
    retirement_calculation_allowed: bool = False


CAREER_STATEMENT_SAFETY_CONTRACT = CareerStatementSafetyContract()


class CareerStatementPort(Protocol):
    """Stable public methods implemented by CareerStatementConnector."""

    def create_empty_statement(self, statement_id: str, imported_at: str = "1970-01-01", source=None) -> CareerStatement: ...

    def validate_statement(self, statement: CareerStatement) -> CareerStatementValidation: ...

    def convert_to_import_batch(self, statement: CareerStatement) -> ImportBatch: ...

    def generate_import_report(self, statement: CareerStatement, view: CareerStatementReportView) -> CareerStatementReport: ...

    def extract_metadata(self, statement: CareerStatement) -> CareerStatementMetadata: ...

    def prepare_reconstruction(self, statement: CareerStatement) -> CareerStatementImport: ...


__all__ = (
    "CareerStatementPort",
    "CAREER_STATEMENT_SAFETY_CONTRACT",
)
