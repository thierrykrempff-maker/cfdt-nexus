"""Synthetic tests for the offline Employment Contract Connector."""

from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_import_models import (
    ImportedCareerRecord,
    ImportedEmploymentPeriod,
    ImportedEvidence,
)
from RETIREMENT_PENIBILITY_ENGINE.employment_contract_connector import EmploymentContractConnector
from RETIREMENT_PENIBILITY_ENGINE.employment_contract_contract import (
    EMPLOYMENT_CONTRACT_SAFETY_CONTRACT,
    EmploymentContractPort,
)
from RETIREMENT_PENIBILITY_ENGINE.employment_contract_models import (
    EmploymentAmendment,
    EmploymentClassification,
    EmploymentCoefficient,
    EmploymentConfidence,
    EmploymentContract,
    EmploymentEmployer,
    EmploymentEvidence,
    EmploymentFiveShift,
    EmploymentMetadata,
    EmploymentNightWork,
    EmploymentPeriod,
    EmploymentPosition,
    EmploymentReportView,
    EmploymentSchedule,
    EmploymentSite,
    EmploymentStatus,
    EmploymentWorkingTime,
)


def contract():
    return EmploymentContract(
        EmploymentMetadata("contract-1", "opaque-contract-reference", "2026-07-21", "v1", EmploymentConfidence.MEDIUM),
        EmploymentEmployer("employer-1", "Employeur synthetique", "employer-reference"),
        sites=(EmploymentSite("site-1", "employer-1", "Site synthetique"),),
        periods=(EmploymentPeriod("period-1", "employer-1", "site-1", "2020-01-01", "2021-12-31"),),
        positions=(EmploymentPosition("position-1", "period-1", "Poste synthetique", "2020-01-01"),),
        classifications=(EmploymentClassification("classification-1", "period-1", "Classification synthetique", "2020-01-01"),),
        coefficients=(EmploymentCoefficient("coefficient-1", "classification-1", "100", "2020-01-01"),),
        schedules=(EmploymentSchedule("schedule-1", "period-1", "Horaire synthetique", "2020-01-01"),),
        working_times=(EmploymentWorkingTime("working-1", "schedule-1", "35.00"),),
        five_shift=(EmploymentFiveShift("five-1", "schedule-1"),),
        night_work=(EmploymentNightWork("night-1", "period-1", True, "NUIT-SYNTHETIQUE"),),
        amendments=(EmploymentAmendment("amendment-1", "v2", "2020-06-01", "v1", ("CLASSIFICATION",), ("evidence-2",)),),
        evidence=(
            EmploymentEvidence("evidence-1", "CONTRACT", "opaque-contract-evidence"),
            EmploymentEvidence("evidence-2", "AMENDMENT", "opaque-amendment-evidence"),
        ),
    )


def test_create_empty_contract_is_synthetic_and_architecture_only():
    empty = EmploymentContractConnector().create_empty_contract("empty-1")
    assert empty.status is EmploymentStatus.EMPTY
    assert empty.metadata.synthetic_only is True
    assert empty.periods == empty.amendments == ()


def test_public_contract_is_disabled_and_compatible_with_existing_engines():
    assert hasattr(EmploymentContractPort, "extract_contract_information")
    assert EMPLOYMENT_CONTRACT_SAFETY_CONTRACT.status == "ARCHITECTURE_ONLY"
    assert EMPLOYMENT_CONTRACT_SAFETY_CONTRACT.enabled is False
    assert not any(
        (
            EMPLOYMENT_CONTRACT_SAFETY_CONTRACT.network_allowed,
            EMPLOYMENT_CONTRACT_SAFETY_CONTRACT.pdf_parsing_allowed,
            EMPLOYMENT_CONTRACT_SAFETY_CONTRACT.ocr_allowed,
            EMPLOYMENT_CONTRACT_SAFETY_CONTRACT.api_allowed,
            EMPLOYMENT_CONTRACT_SAFETY_CONTRACT.real_documents_allowed,
        )
    )
    assert all(
        (
            EMPLOYMENT_CONTRACT_SAFETY_CONTRACT.career_statement_compatible,
            EMPLOYMENT_CONTRACT_SAFETY_CONTRACT.payslip_compatible,
            EMPLOYMENT_CONTRACT_SAFETY_CONTRACT.career_import_compatible,
            EMPLOYMENT_CONTRACT_SAFETY_CONTRACT.career_reconstruction_compatible,
            EMPLOYMENT_CONTRACT_SAFETY_CONTRACT.career_timeline_compatible,
            EMPLOYMENT_CONTRACT_SAFETY_CONTRACT.career_evidence_compatible,
            EMPLOYMENT_CONTRACT_SAFETY_CONTRACT.potential_rights_compatible,
        )
    )


def test_complete_synthetic_contract_is_structurally_valid():
    result = EmploymentContractConnector().validate_contract(contract())
    assert result.valid is True
    assert result.status is EmploymentStatus.VALID


@pytest.mark.parametrize(
    "changed, issue_type",
    [
        (lambda item: replace(item, periods=(replace(item.periods[0], start_date="invalid"),)), "INVALID_DATE"),
        (lambda item: replace(item, periods=(replace(item.periods[0], start_date="2022-01-01"),)), "CHRONOLOGICAL_ORDER"),
        (lambda item: replace(item, positions=(replace(item.positions[0], label=None),)), "MISSING_POSITION"),
        (lambda item: replace(item, classifications=(replace(item.classifications[0], label=None),)), "MISSING_CLASSIFICATION"),
        (lambda item: replace(item, coefficients=(replace(item.coefficients[0], value=None),)), "MISSING_COEFFICIENT"),
        (lambda item: replace(item, schedules=(replace(item.schedules[0], label=None),)), "MISSING_SCHEDULE"),
        (lambda item: replace(item, working_times=(replace(item.working_times[0], declared_hours="-1"),)), "INVALID_WORKING_TIME"),
        (lambda item: replace(item, five_shift=(replace(item.five_shift[0], schedule_id="missing"),)), "UNKNOWN_SCHEDULE"),
        (lambda item: replace(item, amendments=(replace(item.amendments[0], supersedes_version="other"),)), "INVALID_VERSION_CHAIN"),
        (lambda item: replace(item, amendments=(replace(item.amendments[0], change_types=()),)), "EMPTY_AMENDMENT"),
    ],
)
def test_validation_detects_expected_structural_issues(changed, issue_type):
    result = EmploymentContractConnector().validate_contract(changed(contract()))
    assert result.valid is False
    assert issue_type in {item.issue_type for item in result.issues}


def test_successive_amendments_require_unique_ordered_version_chain():
    original = contract()
    second = EmploymentAmendment("amendment-2", "v3", "2020-09-01", "v2", ("SCHEDULE",), ("evidence-2",))
    valid = replace(original, amendments=original.amendments + (second,))
    assert EmploymentContractConnector().validate_contract(valid).valid is True
    broken = replace(valid, amendments=valid.amendments + (replace(second, amendment_id="amendment-3"),))
    issue_types = {item.issue_type for item in EmploymentContractConnector().validate_contract(broken).issues}
    assert "DUPLICATE_VERSION" in issue_types


def test_duplicate_identifiers_are_retained_for_review():
    original = contract()
    duplicate = replace(original.positions[0], label="Autre poste")
    changed = replace(original, positions=original.positions + (duplicate,))
    result = EmploymentContractConnector().validate_contract(changed)
    assert any(item.issue_type == "DUPLICATE" for item in result.issues)
    assert len(changed.positions) == 2


def test_conversion_builds_all_required_career_import_record_types():
    batch = EmploymentContractConnector().convert_to_import_batch(contract())
    assert {ImportedEmploymentPeriod, ImportedCareerRecord, ImportedEvidence} <= {type(item) for item in batch.records}
    assert batch.synthetic_only is True


def test_conversion_preserves_provenance_versions_and_immutability():
    original = contract()
    batch = EmploymentContractConnector().convert_to_import_batch(original)
    assert all(item.provenance.internal_document_id == "opaque-contract-reference" for item in batch.records)
    amendment = next(item for item in batch.records if item.record_id == "amendment-1")
    assert dict(amendment.original_values)["version"] == "v2"
    with pytest.raises(FrozenInstanceError):
        original.metadata.version = "v3"


def test_extract_contract_information_covers_classification_schedule_and_five_shift():
    info = EmploymentContractConnector().extract_contract_information(contract())
    assert info.classifications == ("Classification synthetique",)
    assert info.coefficients == ("100",)
    assert info.schedules == ("Horaire synthetique",)
    assert info.working_times == ("35.00",)
    assert info.five_shift_ids == ("five-1",)


def test_real_contract_metadata_fails_closed_before_conversion():
    original = contract()
    invalid = replace(original, metadata=replace(original.metadata, synthetic_only=False))
    with pytest.raises(ValueError):
        EmploymentContractConnector().convert_to_import_batch(invalid)


def test_employee_and_expert_reports_are_distinct():
    connector = EmploymentContractConnector()
    employee = connector.generate_import_report(contract(), EmploymentReportView.EMPLOYEE_VIEW)
    expert = connector.generate_import_report(contract(), EmploymentReportView.EXPERT_VIEW)
    assert employee.detected_contracts == ("contract-1",)
    assert employee.detected_amendments == ("amendment-1",)
    assert employee.provenance == ()
    assert expert.provenance == ("opaque-contract-reference",)
    assert expert.classifications == ("Classification synthetique",)
    assert expert.career_import_preparation


def test_prepare_reconstruction_remains_a_human_validated_proposal():
    prepared = EmploymentContractConnector().prepare_reconstruction(contract())
    assert prepared.reconstruction_proposal is not None
    assert prepared.reconstruction_proposal.validation_requirement.completed is False
    assert prepared.import_batch.synthetic_only is True


def test_connector_sources_have_no_network_pdf_ocr_api_or_document_reader():
    package = Path(__file__).parents[1] / "RETIREMENT_PENIBILITY_ENGINE"
    sources = "\n".join(path.read_text(encoding="utf-8") for path in package.glob("employment_contract_*.py"))
    forbidden = (
        "import requests", "import urllib", "import http", "import ssl", "socket",
        "HTMLParser", "ElementTree", "pdfplumber", "pypdf", "pytesseract", "open(",
    )
    assert not any(marker in sources for marker in forbidden)
