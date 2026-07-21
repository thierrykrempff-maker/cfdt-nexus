"""Synthetic architecture tests for the Career Statement Connector."""

from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_import_models import (
    ImportedCareerRecord,
    ImportedEmploymentPeriod,
    ImportedEvidence,
)
from RETIREMENT_PENIBILITY_ENGINE.career_statement_connector import CareerStatementConnector
from RETIREMENT_PENIBILITY_ENGINE.career_statement_contract import (
    CAREER_STATEMENT_SAFETY_CONTRACT,
    CareerStatementPort,
)
from RETIREMENT_PENIBILITY_ENGINE.career_statement_models import (
    CareerStatement,
    CareerStatementConfidence,
    CareerStatementEmployer,
    CareerStatementEmployment,
    CareerStatementHeader,
    CareerStatementMetadata,
    CareerStatementPeriod,
    CareerStatementPrecision,
    CareerStatementReference,
    CareerStatementReportView,
    CareerStatementSource,
    CareerStatementStatus,
)


def statement():
    metadata = CareerStatementMetadata(
        "statement-1",
        CareerStatementSource.SYNTHETIC_TEST,
        "opaque-statement-reference",
        "2026-01-01",
        "2026-07-21",
        "v1",
        CareerStatementConfidence.MEDIUM,
    )
    reference = CareerStatementReference("reference-1", "SYNTHETIC_REFERENCE", "opaque-reference-1")
    employer = CareerStatementEmployer("employer-1", "Employeur synthetique", "employer-reference-1")
    employment = CareerStatementEmployment(
        "employment-1",
        employer.employer_id,
        "2001-01-01",
        "2001-12-31",
        CareerStatementPrecision.EXACT,
        CareerStatementPrecision.EXACT,
        (reference.reference_id,),
    )
    period = CareerStatementPeriod(
        "period-1",
        "COMPANY_ENTRY",
        "2001",
        None,
        CareerStatementPrecision.YEAR_ONLY,
        CareerStatementPrecision.UNKNOWN,
        "Evenement synthetique",
        (reference.reference_id,),
    )
    return CareerStatement(metadata, CareerStatementHeader("general", "2026-01-01", 2), (employer,), (employment,), (period,), (reference,))


def test_empty_statement_is_synthetic_and_contains_no_records():
    empty = CareerStatementConnector().create_empty_statement("empty-1")
    assert empty.status is CareerStatementStatus.EMPTY
    assert empty.metadata.synthetic_only is True
    assert empty.employments == empty.periods == empty.references == ()


def test_contract_is_architecture_only_and_disabled():
    assert hasattr(CareerStatementPort, "prepare_reconstruction")
    assert CAREER_STATEMENT_SAFETY_CONTRACT.status == "ARCHITECTURE_ONLY"
    assert CAREER_STATEMENT_SAFETY_CONTRACT.enabled is False
    assert not any(
        (
            CAREER_STATEMENT_SAFETY_CONTRACT.network_allowed,
            CAREER_STATEMENT_SAFETY_CONTRACT.carsat_api_allowed,
            CAREER_STATEMENT_SAFETY_CONTRACT.cnav_api_allowed,
            CAREER_STATEMENT_SAFETY_CONTRACT.france_connect_allowed,
            CAREER_STATEMENT_SAFETY_CONTRACT.pdf_parsing_allowed,
            CAREER_STATEMENT_SAFETY_CONTRACT.ocr_allowed,
        )
    )


def test_valid_statement_passes_structural_validation():
    validation = CareerStatementConnector().validate_statement(statement())
    assert validation.valid is True
    assert validation.status is CareerStatementStatus.VALID
    assert validation.issues == validation.conflicts == ()


@pytest.mark.parametrize(
    "changed, issue_type",
    [
        (lambda item: replace(item, employments=(replace(item.employments[0], employer_id="missing"),)), "UNKNOWN_EMPLOYER"),
        (lambda item: replace(item, periods=(replace(item.periods[0], start_date="20XX"),)), "INVALID_DATE_FORMAT"),
        (lambda item: replace(item, employments=(replace(item.employments[0], start_date="2002-01-01"),)), "CHRONOLOGICAL_ORDER"),
        (lambda item: replace(item, periods=(replace(item.periods[0], start_date=None, end_date=None),)), "EMPTY_PERIOD"),
        (lambda item: replace(item, periods=(replace(item.periods[0], reference_ids=("missing",)),)), "MISSING_REFERENCE"),
    ],
)
def test_validation_detects_expected_structural_issues(changed, issue_type):
    result = CareerStatementConnector().validate_statement(changed(statement()))
    assert result.valid is False
    assert issue_type in {item.issue_type for item in result.issues}


def test_duplicates_are_retained_as_conflicts():
    original = statement()
    duplicate = replace(original.employments[0], employment_id="employment-2")
    result = CareerStatementConnector().validate_statement(replace(original, employments=original.employments + (duplicate,)))
    assert result.valid is False
    assert any(item.conflict_type == "DUPLICATE" for item in result.conflicts)


def test_conversion_creates_all_required_import_record_types():
    batch = CareerStatementConnector().convert_to_import_batch(statement())
    assert {type(item) for item in batch.records} == {ImportedCareerRecord, ImportedEmploymentPeriod, ImportedEvidence}
    assert batch.synthetic_only is True


def test_conversion_preserves_provenance_and_date_precision_without_mutation():
    original = statement()
    batch = CareerStatementConnector().convert_to_import_batch(original)
    assert all(item.provenance.internal_document_id == "opaque-statement-reference" for item in batch.records)
    career_record = next(item for item in batch.records if isinstance(item, ImportedCareerRecord))
    values = dict(career_record.original_values)
    assert values["start_date"] == "2001"
    assert values["start_precision"] == "YEAR_ONLY"
    assert original.periods[0].start_date == "2001"
    with pytest.raises(FrozenInstanceError):
        original.metadata.version = "v2"


def test_invalid_statement_fails_closed_before_conversion():
    invalid = replace(statement(), metadata=replace(statement().metadata, synthetic_only=False))
    with pytest.raises(ValueError):
        CareerStatementConnector().convert_to_import_batch(invalid)


def test_employee_and_expert_reports_are_distinct():
    connector = CareerStatementConnector()
    employee = connector.generate_import_report(statement(), CareerStatementReportView.EMPLOYEE_VIEW)
    expert = connector.generate_import_report(statement(), CareerStatementReportView.EXPERT_VIEW)
    assert employee.recognized_periods == ("employment-1", "period-1")
    assert employee.metadata == ()
    assert expert.metadata and expert.provenance == ("opaque-statement-reference",)
    assert expert.import_preparation == ("employment-1", "period-1", "reference-1")


def test_extract_metadata_returns_the_immutable_declared_metadata():
    original = statement()
    assert CareerStatementConnector().extract_metadata(original) is original.metadata


def test_prepare_reconstruction_uses_existing_import_and_reconstruction_engines():
    prepared = CareerStatementConnector().prepare_reconstruction(statement())
    assert prepared.conversion.import_batch.batch_id == "career-statement:statement-1"
    assert prepared.reconstruction_proposal is not None
    assert prepared.reconstruction_proposal.validation_requirement.completed is False


def test_connector_sources_have_no_network_pdf_ocr_or_file_reading_code():
    package = Path(__file__).parents[1] / "RETIREMENT_PENIBILITY_ENGINE"
    sources = "\n".join(path.read_text(encoding="utf-8") for path in package.glob("career_statement_*.py"))
    forbidden = (
        "import requests",
        "import urllib",
        "import http",
        "import ssl",
        "socket",
        "HTMLParser",
        "ElementTree",
        "pdfplumber",
        "pypdf",
        "pytesseract",
        "open(",
    )
    assert not any(marker in sources for marker in forbidden)
