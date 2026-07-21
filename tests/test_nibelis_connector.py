"""Synthetic architecture tests for the offline Nibelis Connector."""

from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_import_models import (
    ImportedCareerRecord,
    ImportedEmploymentPeriod,
    ImportedEvidence,
)
from RETIREMENT_PENIBILITY_ENGINE.nibelis_connector import InjectedNibelisReferentialLookup, NibelisConnector
from RETIREMENT_PENIBILITY_ENGINE.nibelis_contract import (
    NIBELIS_REFERENTIAL_COMPATIBILITY,
    NIBELIS_SAFETY_CONTRACT,
    NibelisPort,
)
from RETIREMENT_PENIBILITY_ENGINE.nibelis_models import (
    NibelisClassification,
    NibelisCoefficient,
    NibelisConfidence,
    NibelisContribution,
    NibelisEmployer,
    NibelisEvidence,
    NibelisExport,
    NibelisMetadata,
    NibelisPayrollParameter,
    NibelisPayrollPeriod,
    NibelisReportView,
    NibelisSalaryItem,
    NibelisStatus,
)


RUBRIC_IDS = frozenset(("NIB_RUB_SALAIRE_BASE", "NIB_RUB_HSUP_BASE"))
PARAMETER_IDS = frozenset(("PARAM_DUREE_MENSUELLE_REF_SYN",))


def connector():
    return NibelisConnector(InjectedNibelisReferentialLookup(RUBRIC_IDS, PARAMETER_IDS))


def nibelis_export():
    return NibelisExport(
        NibelisMetadata("export-1", "opaque-export-reference", "2026-07-21", "v1", NibelisConfidence.MEDIUM),
        NibelisEmployer("employer-1", "Employeur synthetique", "employer-reference"),
        periods=(NibelisPayrollPeriod("period-1", "employer-1", "2026-01-01", "2026-01-31"),),
        salary_items=(NibelisSalaryItem("salary-1", "period-1", "NIB_RUB_SALAIRE_BASE", "1000.00", "1000.00", None, None),),
        contributions=(NibelisContribution("contribution-1", "period-1", "NIB_RUB_HSUP_BASE", "100.00"),),
        parameters=(NibelisPayrollParameter("parameter-1", "period-1", "PARAM_DUREE_MENSUELLE_REF_SYN", "151.67"),),
        classifications=(NibelisClassification("classification-1", "period-1", "Classification synthetique"),),
        coefficients=(NibelisCoefficient("coefficient-1", "classification-1", "100"),),
        evidence=(NibelisEvidence("evidence-1", "NIBELIS_EXPORT", "opaque-evidence-reference"),),
    )


def test_create_empty_export_is_synthetic_and_contains_no_payroll_data():
    empty = NibelisConnector().create_empty_export("empty-1")
    assert empty.status is NibelisStatus.EMPTY
    assert empty.metadata.synthetic_only is True
    assert empty.salary_items == empty.contributions == ()


def test_public_contract_is_disabled_and_compatible_with_existing_engines():
    assert hasattr(NibelisPort, "extract_payroll_data")
    assert NIBELIS_SAFETY_CONTRACT.status == "ARCHITECTURE_ONLY"
    assert NIBELIS_SAFETY_CONTRACT.enabled is False
    assert not any(
        (
            NIBELIS_SAFETY_CONTRACT.network_allowed,
            NIBELIS_SAFETY_CONTRACT.file_reading_allowed,
            NIBELIS_SAFETY_CONTRACT.export_parsing_allowed,
            NIBELIS_SAFETY_CONTRACT.payslip_parsing_allowed,
            NIBELIS_SAFETY_CONTRACT.ocr_allowed,
            NIBELIS_SAFETY_CONTRACT.api_allowed,
            NIBELIS_SAFETY_CONTRACT.nibelis_access_allowed,
        )
    )
    assert NIBELIS_SAFETY_CONTRACT.existing_nibelis_referential_required is True
    assert all(
        (
            NIBELIS_SAFETY_CONTRACT.career_statement_compatible,
            NIBELIS_SAFETY_CONTRACT.payslip_compatible,
            NIBELIS_SAFETY_CONTRACT.employment_contract_compatible,
            NIBELIS_SAFETY_CONTRACT.kelio_compatible,
            NIBELIS_SAFETY_CONTRACT.career_import_compatible,
            NIBELIS_SAFETY_CONTRACT.career_reconstruction_compatible,
            NIBELIS_SAFETY_CONTRACT.potential_rights_compatible,
        )
    )


def test_existing_nibelis_referential_locations_are_reused_not_remodelled():
    assert NIBELIS_REFERENTIAL_COMPATIBILITY.referential_kind == "nibelis"
    assert NIBELIS_REFERENTIAL_COMPATIBILITY.identifier_field == "rubric_id"
    assert NIBELIS_REFERENTIAL_COMPATIBILITY.schema_path.endswith("nibelis-rubrics.schema.json")
    assert NIBELIS_REFERENTIAL_COMPATIBILITY.validator_module == "automation.payroll.payroll_referential_validator"


def test_complete_synthetic_export_is_structurally_valid():
    result = connector().validate_export(nibelis_export())
    assert result.valid is True
    assert result.status is NibelisStatus.VALID


def test_referential_lookup_is_mandatory_for_payroll_occurrences():
    result = NibelisConnector().validate_export(nibelis_export())
    assert result.valid is False
    assert "REFERENTIAL_LOOKUP_REQUIRED" in {item.issue_type for item in result.issues}


@pytest.mark.parametrize(
    "changed, issue_type",
    [
        (lambda item: replace(item, periods=(replace(item.periods[0], start_date="invalid"),)), "INVALID_DATE"),
        (lambda item: replace(item, periods=(replace(item.periods[0], start_date="2026-02-01"),)), "CHRONOLOGICAL_ORDER"),
        (lambda item: replace(item, salary_items=(replace(item.salary_items[0], period_id="missing"),)), "UNKNOWN_PERIOD"),
        (lambda item: replace(item, salary_items=(replace(item.salary_items[0], referential_rubric_id="UNKNOWN"),)), "UNKNOWN_RUBRIC_REFERENCE"),
        (lambda item: replace(item, salary_items=(replace(item.salary_items[0], declared_amount="invalid"),)), "INVALID_DECLARED_VALUE"),
        (lambda item: replace(item, parameters=(replace(item.parameters[0], referential_parameter_id="UNKNOWN"),)), "UNKNOWN_PARAMETER_REFERENCE"),
        (lambda item: replace(item, classifications=(replace(item.classifications[0], label=None),)), "MISSING_CLASSIFICATION"),
        (lambda item: replace(item, coefficients=(replace(item.coefficients[0], value=None),)), "MISSING_COEFFICIENT"),
    ],
)
def test_validation_detects_expected_structural_issues(changed, issue_type):
    result = connector().validate_export(changed(nibelis_export()))
    assert result.valid is False
    assert issue_type in {item.issue_type for item in result.issues}


def test_duplicate_occurrence_identifiers_are_retained_for_review():
    original = nibelis_export()
    duplicate = replace(original.salary_items[0], declared_amount="2000.00")
    changed = replace(original, salary_items=original.salary_items + (duplicate,))
    result = connector().validate_export(changed)
    assert any(item.issue_type == "DUPLICATE" for item in result.issues)
    assert len(changed.salary_items) == 2


def test_conversion_builds_required_career_import_record_types():
    batch = connector().convert_to_import_batch(nibelis_export())
    assert {ImportedEmploymentPeriod, ImportedCareerRecord, ImportedEvidence} <= {type(item) for item in batch.records}
    assert batch.synthetic_only is True


def test_conversion_preserves_referential_ids_provenance_and_immutability():
    original = nibelis_export()
    batch = connector().convert_to_import_batch(original)
    assert all(item.provenance.internal_document_id == "opaque-export-reference" for item in batch.records)
    salary = next(item for item in batch.records if item.record_id == "salary-1")
    assert dict(salary.original_values)["referential_rubric_id"] == "NIB_RUB_SALAIRE_BASE"
    with pytest.raises(FrozenInstanceError):
        original.metadata.version = "v2"


def test_extract_payroll_data_returns_existing_referential_ids_only():
    information = connector().extract_payroll_data(nibelis_export())
    assert information.rubric_ids == ("NIB_RUB_SALAIRE_BASE", "NIB_RUB_HSUP_BASE")
    assert information.parameter_ids == ("PARAM_DUREE_MENSUELLE_REF_SYN",)
    assert information.classifications == ("Classification synthetique",)


def test_real_export_fails_closed_before_conversion():
    original = nibelis_export()
    invalid = replace(original, metadata=replace(original.metadata, synthetic_only=False))
    with pytest.raises(ValueError):
        connector().convert_to_import_batch(invalid)


def test_employee_and_expert_reports_are_distinct():
    employee = connector().generate_import_report(nibelis_export(), NibelisReportView.EMPLOYEE_VIEW)
    expert = connector().generate_import_report(nibelis_export(), NibelisReportView.EXPERT_VIEW)
    assert employee.recognized_periods == ("period-1",)
    assert employee.detected_rubrics == ("NIB_RUB_SALAIRE_BASE", "NIB_RUB_HSUP_BASE")
    assert employee.provenance == ()
    assert expert.provenance == ("opaque-export-reference",)
    assert expert.parameters == ("PARAM_DUREE_MENSUELLE_REF_SYN",)
    assert expert.career_import_preparation


def test_prepare_reconstruction_remains_a_human_validated_proposal():
    prepared = connector().prepare_reconstruction(nibelis_export())
    assert prepared.reconstruction_proposal is not None
    assert prepared.reconstruction_proposal.validation_requirement.completed is False
    assert prepared.import_batch.synthetic_only is True


def test_connector_sources_have_no_network_pdf_ocr_api_or_export_reader():
    package = Path(__file__).parents[1] / "RETIREMENT_PENIBILITY_ENGINE"
    sources = "\n".join(path.read_text(encoding="utf-8") for path in package.glob("nibelis_*.py"))
    forbidden = (
        "import requests", "import urllib", "import http", "import ssl", "socket",
        "HTMLParser", "ElementTree", "pdfplumber", "pypdf", "pytesseract", "open(",
    )
    assert not any(marker in sources for marker in forbidden)
