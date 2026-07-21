"""Synthetic architecture tests for the offline Payslip Connector."""

from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_import_models import (
    ImportedCareerRecord,
    ImportedEmploymentPeriod,
    ImportedEvidence,
)
from RETIREMENT_PENIBILITY_ENGINE.payslip_connector import PayslipConnector
from RETIREMENT_PENIBILITY_ENGINE.payslip_contract import PAYSLIP_SAFETY_CONTRACT, PayslipPort
from RETIREMENT_PENIBILITY_ENGINE.payslip_models import (
    Payslip,
    PayslipAbsence,
    PayslipClassification,
    PayslipCoefficient,
    PayslipConfidence,
    PayslipContribution,
    PayslipEmployee,
    PayslipEmployer,
    PayslipEvidence,
    PayslipFiveShift,
    PayslipHeader,
    PayslipMetadata,
    PayslipNightWork,
    PayslipOvertime,
    PayslipPeriod,
    PayslipReportView,
    PayslipSalaryItem,
    PayslipStatus,
    PayslipWorkingTime,
)


def payslip():
    return Payslip(
        PayslipMetadata("payslip-1", "opaque-payslip-reference", "2026-07-21", "v1", PayslipConfidence.MEDIUM),
        PayslipHeader("2026-02-01", "2026-01-01", "2026-01-31"),
        PayslipEmployee("synthetic-employee-1"),
        PayslipEmployer("employer-1", "Employeur synthetique", "employer-reference"),
        periods=(PayslipPeriod("period-1", "employer-1", "2026-01-01", "2026-01-31"),),
        working_times=(PayslipWorkingTime("working-1", "period-1", "151.67", "HORAIRE-SYNTHETIQUE"),),
        night_work=(PayslipNightWork("night-1", "period-1", "12.00"),),
        five_shift=(PayslipFiveShift("five-1", "period-1", "5X8-SYNTHETIQUE"),),
        classifications=(PayslipClassification("classification-1", "period-1", "CLASSIFICATION-SYNTHETIQUE"),),
        coefficients=(PayslipCoefficient("coefficient-1", "classification-1", "100"),),
        salary_items=(PayslipSalaryItem("salary-1", "BASE", "Rubrique synthetique", "1000.00"),),
        contributions=(PayslipContribution("contribution-1", "COT", "Cotisation synthetique", "100.00"),),
        absences=(PayslipAbsence("absence-1", "period-1", "ABSENCE-SYNTHETIQUE", "1.00"),),
        overtime=(PayslipOvertime("overtime-1", "period-1", "2.00", "RATE-SYNTHETIQUE"),),
        evidence=(PayslipEvidence("evidence-1", "PAYSLIP", "opaque-evidence-reference"),),
    )


def test_create_empty_payslip_is_anonymous_and_synthetic():
    empty = PayslipConnector().create_empty_payslip("empty-1")
    assert empty.status is PayslipStatus.EMPTY
    assert empty.metadata.synthetic_only is True
    assert empty.employee.anonymized is True
    assert empty.periods == ()


def test_contract_is_disabled_and_declares_expected_compatibilities():
    assert hasattr(PayslipPort, "extract_payroll_information")
    assert PAYSLIP_SAFETY_CONTRACT.status == "ARCHITECTURE_ONLY"
    assert PAYSLIP_SAFETY_CONTRACT.enabled is False
    assert not any(
        (
            PAYSLIP_SAFETY_CONTRACT.network_allowed,
            PAYSLIP_SAFETY_CONTRACT.pdf_parsing_allowed,
            PAYSLIP_SAFETY_CONTRACT.ocr_allowed,
            PAYSLIP_SAFETY_CONTRACT.api_allowed,
            PAYSLIP_SAFETY_CONTRACT.nibelis_access_allowed,
            PAYSLIP_SAFETY_CONTRACT.kelio_access_allowed,
        )
    )
    assert all(
        (
            PAYSLIP_SAFETY_CONTRACT.career_import_compatible,
            PAYSLIP_SAFETY_CONTRACT.career_reconstruction_compatible,
            PAYSLIP_SAFETY_CONTRACT.expert_paie_v2_compatible,
            PAYSLIP_SAFETY_CONTRACT.nibelis_referential_compatible,
            PAYSLIP_SAFETY_CONTRACT.kelio_referential_compatible,
            PAYSLIP_SAFETY_CONTRACT.potential_rights_compatible,
        )
    )


def test_complete_synthetic_payslip_is_structurally_valid():
    result = PayslipConnector().validate_payslip(payslip())
    assert result.valid is True
    assert result.status is PayslipStatus.VALID


@pytest.mark.parametrize(
    "changed, issue_type",
    [
        (lambda item: replace(item, periods=(replace(item.periods[0], start_date="invalid"),)), "INVALID_DATE"),
        (lambda item: replace(item, periods=(replace(item.periods[0], start_date="2026-02-01"),)), "CHRONOLOGICAL_ORDER"),
        (lambda item: replace(item, classifications=(replace(item.classifications[0], label=None),)), "MISSING_CLASSIFICATION"),
        (lambda item: replace(item, coefficients=(replace(item.coefficients[0], value=None),)), "MISSING_COEFFICIENT"),
        (lambda item: replace(item, working_times=(replace(item.working_times[0], declared_hours="-1"),)), "INVALID_WORKING_TIME"),
        (lambda item: replace(item, salary_items=(replace(item.salary_items[0], code=None, label=None),)), "INVALID_PAYROLL_ITEM"),
    ],
)
def test_structural_validation_detects_expected_issues(changed, issue_type):
    result = PayslipConnector().validate_payslip(changed(payslip()))
    assert result.valid is False
    assert issue_type in {item.issue_type for item in result.issues}


def test_duplicate_identifiers_are_rejected_without_deletion():
    original = payslip()
    duplicate = replace(original.salary_items[0], label="Autre rubrique")
    changed = replace(original, salary_items=original.salary_items + (duplicate,))
    result = PayslipConnector().validate_payslip(changed)
    assert any(item.issue_type == "DUPLICATE" for item in result.issues)
    assert len(changed.salary_items) == 2


def test_conversion_builds_required_import_record_types():
    batch = PayslipConnector().convert_to_import_batch(payslip())
    assert {ImportedEmploymentPeriod, ImportedCareerRecord, ImportedEvidence} <= {type(item) for item in batch.records}
    assert batch.synthetic_only is True


def test_conversion_preserves_provenance_and_original_immutability():
    original = payslip()
    batch = PayslipConnector().convert_to_import_batch(original)
    assert all(item.provenance.internal_document_id == "opaque-payslip-reference" for item in batch.records)
    assert all(item.provenance.document_type.value == "PAYSLIP" for item in batch.records)
    assert original.working_times[0].declared_hours == "151.67"
    with pytest.raises(FrozenInstanceError):
        original.metadata.version = "v2"


def test_extract_payroll_information_is_metadata_only():
    extracted = PayslipConnector().extract_payroll_information(payslip())
    assert extracted.period_ids == ("period-1",)
    assert extracted.classification_labels == ("CLASSIFICATION-SYNTHETIQUE",)
    assert extracted.night_work_ids == ("night-1",)
    assert extracted.five_shift_ids == ("five-1",)
    assert extracted.salary_item_codes == ("BASE",)


def test_invalid_real_payslip_fails_closed_before_conversion():
    original = payslip()
    invalid = replace(original, metadata=replace(original.metadata, synthetic_only=False))
    with pytest.raises(ValueError):
        PayslipConnector().convert_to_import_batch(invalid)


def test_employee_and_expert_reports_are_distinct():
    connector = PayslipConnector()
    employee = connector.generate_import_report(payslip(), PayslipReportView.EMPLOYEE_VIEW)
    expert = connector.generate_import_report(payslip(), PayslipReportView.EXPERT_VIEW)
    assert employee.recognized_periods == ("period-1",)
    assert employee.provenance == ()
    assert expert.provenance == ("opaque-payslip-reference",)
    assert expert.classifications == ("CLASSIFICATION-SYNTHETIQUE", "100")
    assert expert.career_import_preparation


def test_prepare_reconstruction_requires_future_human_validation():
    prepared = PayslipConnector().prepare_reconstruction(payslip())
    assert prepared.reconstruction_proposal is not None
    assert prepared.reconstruction_proposal.validation_requirement.completed is False
    assert prepared.import_batch.synthetic_only is True


def test_connector_sources_have_no_network_pdf_ocr_or_api_implementation():
    package = Path(__file__).parents[1] / "RETIREMENT_PENIBILITY_ENGINE"
    sources = "\n".join(path.read_text(encoding="utf-8") for path in package.glob("payslip_*.py"))
    forbidden = (
        "import requests", "import urllib", "import http", "import ssl", "socket",
        "HTMLParser", "ElementTree", "pdfplumber", "pypdf", "pytesseract", "open(",
    )
    assert not any(marker in sources for marker in forbidden)
