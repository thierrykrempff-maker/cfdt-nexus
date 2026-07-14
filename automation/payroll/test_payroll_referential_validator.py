#!/usr/bin/env python
"""Tests for LOT 4A payroll referential validation.

All data used here is synthetic. The tests exercise the production validator
without network access and without reading any private payroll document.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from automation.payroll import payroll_referential_validator as validator  # noqa: E402


EXPECTED_KELIO_CODES = {
    "JR_SYN",
    "RJFJ_SYN",
    "RJFN_SYN",
    "RCTP_SYN",
    "RCTR_SYN",
    "CP_SYN",
    "HS_SYN",
    "AST_SYN",
    "INT_SYN",
    "RC_SYN",
    "RQ_SYN",
    "RH_SYN",
    "PNT_SYN",
    "ABS_SYN",
    "NUIT_SYN",
    "DIM_SYN",
    "FERIE_SYN",
}

EXPECTED_NIBELIS_CODES = {
    "BASE_SAL_SYN",
    "ANC_SYN",
    "POSTE_5X8_SYN",
    "HS_BASE_SYN",
    "HS_MAJ_SYN",
    "NUIT_SYN",
    "DIM_SYN",
    "FERIE_PAY_SYN",
    "AST_PAY_SYN",
    "INT_AST_SYN",
    "CP_INFO_SYN",
    "ICP_SYN",
    "ABS_NR_SYN",
    "RET_ABS_SYN",
    "MAINT_MAL_SYN",
    "IJSS_SYN",
    "SUBRO_SYN",
    "ATMP_SYN",
    "TREIZE_SYN",
    "PRIME_EXC_SYN",
    "KM_SYN",
    "PANIER_SYN",
    "REPOS_COMP_SYN",
    "REG_PAIE_SYN",
    "RAPPEL_SYN",
    "COMPTEURS_INFO_SYN",
}

REQUIRED_NIBELIS_CATEGORIES = {
    "base_salary",
    "premium",
    "overtime",
    "leave",
    "absence",
    "sickness",
    "on_call",
    "allowance",
    "regularization",
    "counter_information",
}

KELIO_DOCUMENTATION_FIELDS = {
    "business_description",
    "feed_conditions",
    "decrease_conditions",
    "documents_to_check",
    "frequent_anomalies",
    "control_points",
    "synthetic_reading_examples",
}

NIBELIS_DOCUMENTATION_FIELDS = {
    "business_description",
    "generic_source",
    "documents_to_check",
    "frequent_anomalies",
    "control_points",
    "synthetic_reading_examples",
}


def cloned_catalog(kind: str) -> dict[str, Any]:
    return copy.deepcopy(validator.load_catalog(kind))


def report_for(kind: str, catalog: dict[str, Any]) -> dict[str, Any]:
    catalogs = {name: validator.load_catalog(name) for name in validator.REFERENTIALS}
    catalogs[kind] = catalog
    reference_index = validator.default_reference_index(catalogs)
    return validator.validate_catalog(
        kind,
        catalog=catalog,
        schema=validator.load_schema(kind),
        reference_index=reference_index,
    )


def errors(report: dict[str, Any]) -> list[dict[str, Any]]:
    return list(report.get("errors", []))


def assert_issue(report: dict[str, Any], code: str) -> None:
    assert any(issue["code"] == code for issue in errors(report)), report


def assert_no_issue(report: dict[str, Any], code: str) -> None:
    assert not any(issue["code"] == code for issue in errors(report)), report


def find_record(catalog: dict[str, Any], collection: str, field_name: str, value: str) -> dict[str, Any]:
    for record in catalog[collection]:
        if record[field_name] == value:
            return record
    raise AssertionError(f"Missing record {field_name}={value}")


def test_all_example_referentials_validate() -> None:
    report = validator.validate_all()
    assert report["valid"], report
    assert report["reports"]["nibelis"]["records_count"] == 26
    assert report["reports"]["kelio"]["records_count"] == 17
    assert report["reports"]["parameters"]["records_count"] == 3


def test_nibelis_referential_contains_required_synthetic_codes() -> None:
    catalog = cloned_catalog("nibelis")
    codes = {rubric["rubric_code"] for rubric in catalog["rubrics"]}
    assert EXPECTED_NIBELIS_CODES == codes
    assert len(catalog["rubrics"]) >= 25
    assert len(catalog["rubrics"]) == len(codes)


def test_nibelis_referential_covers_required_business_families() -> None:
    catalog = cloned_catalog("nibelis")
    categories = {rubric["category"] for rubric in catalog["rubrics"]}
    assert REQUIRED_NIBELIS_CATEGORIES <= categories


def test_nibelis_records_have_business_documentation() -> None:
    catalog = cloned_catalog("nibelis")
    for rubric in catalog["rubrics"]:
        for field_name in NIBELIS_DOCUMENTATION_FIELDS:
            assert rubric[field_name], (rubric["rubric_id"], field_name)
        for example in rubric["synthetic_reading_examples"]:
            assert example["label"].strip(), rubric["rubric_id"]
            assert example["value"].strip(), rubric["rubric_id"]
            assert example["interpretation"].strip(), rubric["rubric_id"]


def test_nibelis_referential_does_not_activate_calculation() -> None:
    catalog = cloned_catalog("nibelis")
    for rubric in catalog["rubrics"]:
        assert rubric["calculation_allowed"] is False, rubric["rubric_id"]
        assert rubric["synthetic_only"] is True, rubric["rubric_id"]
        assert rubric["source_layer"] == "synthetic_fixture", rubric["rubric_id"]
    report = report_for("nibelis", catalog)
    assert report["valid"], report


def test_nibelis_links_to_existing_rules_variables_and_kelio_only() -> None:
    catalog = cloned_catalog("nibelis")
    linked_rule_ids = {rule_id for rubric in catalog["rubrics"] for rule_id in rubric["linked_rule_ids"]}
    linked_kelio_ids = {counter_id for rubric in catalog["rubrics"] for counter_id in rubric["linked_kelio_counter_ids"]}
    assert "PAY_HSUP_TRANCHES_001" in linked_rule_ids
    assert "KELIO_HS_SYN" in linked_kelio_ids
    report = report_for("nibelis", catalog)
    assert report["valid"], report
    assert_no_issue(report, "unknown_reference")


def test_kelio_referential_contains_required_counter_codes() -> None:
    catalog = cloned_catalog("kelio")
    codes = {counter["counter_code"] for counter in catalog["counters"]}
    assert EXPECTED_KELIO_CODES <= codes
    assert len(catalog["counters"]) == len(codes)


def test_kelio_records_have_business_documentation() -> None:
    catalog = cloned_catalog("kelio")
    for counter in catalog["counters"]:
        assert counter["business_description"].strip(), counter["counter_id"]
        for field_name in KELIO_DOCUMENTATION_FIELDS - {"business_description"}:
            assert counter[field_name], (counter["counter_id"], field_name)
        assert counter["risk_level"] in {"low", "medium", "high"}


def test_kelio_records_have_control_points_and_anomalies() -> None:
    catalog = cloned_catalog("kelio")
    for counter in catalog["counters"]:
        assert len(counter["control_points"]) >= 3, counter["counter_id"]
        assert len(counter["frequent_anomalies"]) >= 3, counter["counter_id"]
        assert len(counter["documents_to_check"]) >= 2, counter["counter_id"]


def test_kelio_referential_does_not_activate_calculation() -> None:
    catalog = cloned_catalog("kelio")
    assert all(counter["calculation_allowed"] is False for counter in catalog["counters"])
    report = report_for("kelio", catalog)
    assert report["valid"], report


def test_reject_kelio_missing_business_documentation() -> None:
    catalog = cloned_catalog("kelio")
    catalog["counters"][0]["control_points"] = []
    report = report_for("kelio", catalog)
    assert_issue(report, "missing_business_documentation")


def test_reject_kelio_synthetic_only_false_in_fixture() -> None:
    catalog = cloned_catalog("kelio")
    catalog["counters"][0]["synthetic_only"] = False
    report = report_for("kelio", catalog)
    assert_issue(report, "synthetic_fixture_not_marked")


def test_reject_nibelis_missing_business_documentation() -> None:
    catalog = cloned_catalog("nibelis")
    catalog["rubrics"][0]["documents_to_check"] = []
    report = report_for("nibelis", catalog)
    assert_issue(report, "missing_business_documentation")


def test_reject_nibelis_synthetic_only_false_in_fixture() -> None:
    catalog = cloned_catalog("nibelis")
    catalog["rubrics"][0]["synthetic_only"] = False
    report = report_for("nibelis", catalog)
    assert_issue(report, "synthetic_fixture_not_marked")


def test_kelio_links_to_existing_rules_and_variables_only() -> None:
    catalog = cloned_catalog("kelio")
    report = report_for("kelio", catalog)
    assert report["valid"], report
    assert_no_issue(report, "unknown_reference")


def test_reject_unknown_catalog_root_field() -> None:
    catalog = cloned_catalog("nibelis")
    catalog["unexpected_field"] = True
    report = report_for("nibelis", catalog)
    assert_issue(report, "unknown_field")


def test_reject_missing_required_record_field() -> None:
    catalog = cloned_catalog("nibelis")
    del catalog["rubrics"][0]["data_role"]
    report = report_for("nibelis", catalog)
    assert_issue(report, "missing_required_field")


def test_reject_wrong_type() -> None:
    catalog = cloned_catalog("kelio")
    catalog["counters"][0]["linked_rule_ids"] = "PAY_HSUP_TRANCHES_001"
    report = report_for("kelio", catalog)
    assert_issue(report, "invalid_type")


def test_reject_invalid_enum() -> None:
    catalog = cloned_catalog("parameters")
    catalog["parameters"][0]["confidence"] = "certain"
    report = report_for("parameters", catalog)
    assert_issue(report, "invalid_enum")


def test_reject_duplicate_identifier() -> None:
    catalog = cloned_catalog("nibelis")
    catalog["rubrics"][1]["rubric_id"] = catalog["rubrics"][0]["rubric_id"]
    report = report_for("nibelis", catalog)
    assert_issue(report, "duplicate_identifier")


def test_reject_duplicate_code() -> None:
    catalog = cloned_catalog("kelio")
    catalog["counters"][1]["counter_code"] = catalog["counters"][0]["counter_code"]
    report = report_for("kelio", catalog)
    assert_issue(report, "duplicate_code")


def test_reject_invalid_date() -> None:
    catalog = cloned_catalog("parameters")
    catalog["parameters"][0]["effective_date"] = "2026-02-30"
    report = report_for("parameters", catalog)
    assert_issue(report, "invalid_date")


def test_reject_effective_date_after_end_date() -> None:
    catalog = cloned_catalog("kelio")
    catalog["counters"][0]["effective_date"] = "2026-01-02"
    catalog["counters"][0]["end_date"] = "2026-01-01"
    report = report_for("kelio", catalog)
    assert_issue(report, "effective_date_after_end_date")


def test_reject_unknown_rule_link() -> None:
    catalog = cloned_catalog("nibelis")
    catalog["rubrics"][0]["linked_rule_ids"] = ["UNKNOWN_RULE"]
    report = report_for("nibelis", catalog)
    assert_issue(report, "unknown_reference")


def test_reject_unknown_variable_link() -> None:
    catalog = cloned_catalog("parameters")
    catalog["parameters"][0]["linked_variables"] = ["unknown_variable"]
    report = report_for("parameters", catalog)
    assert_issue(report, "unknown_reference")


def test_reject_unknown_nibelis_variable_link() -> None:
    catalog = cloned_catalog("nibelis")
    catalog["rubrics"][0]["linked_variables"] = ["unknown_variable"]
    report = report_for("nibelis", catalog)
    assert_issue(report, "unknown_reference")


def test_reject_unknown_cross_referential_link() -> None:
    catalog = cloned_catalog("nibelis")
    catalog["rubrics"][1]["linked_kelio_counter_ids"] = ["KELIO_UNKNOWN"]
    report = report_for("nibelis", catalog)
    assert_issue(report, "unknown_reference")


def test_reject_duplicate_link() -> None:
    catalog = cloned_catalog("parameters")
    catalog["parameters"][0]["linked_rule_ids"] = ["PAY_HSUP_TRANCHES_001", "PAY_HSUP_TRANCHES_001"]
    report = report_for("parameters", catalog)
    assert_issue(report, "duplicate_link")


def test_synthetic_fixture_cannot_enable_calculation() -> None:
    catalog = cloned_catalog("parameters")
    catalog["parameters"][0]["calculation_allowed"] = True
    report = report_for("parameters", catalog)
    assert_issue(report, "synthetic_fixture_cannot_calculate")
    assert_issue(report, "calculation_from_synthetic_fixture")


def test_nibelis_synthetic_fixture_cannot_enable_calculation() -> None:
    catalog = cloned_catalog("nibelis")
    catalog["rubrics"][0]["calculation_allowed"] = True
    report = report_for("nibelis", catalog)
    assert_issue(report, "synthetic_fixture_cannot_calculate")
    assert_issue(report, "calculation_from_synthetic_fixture")


def test_reject_nibelis_retenue_with_positive_impact() -> None:
    catalog = cloned_catalog("nibelis")
    rubric = find_record(catalog, "rubrics", "rubric_code", "RET_ABS_SYN")
    rubric["gross_impact"] = "positive"
    report = report_for("nibelis", catalog)
    assert_issue(report, "nibelis_retenue_must_be_negative")


def test_reject_nibelis_informational_rubric_affecting_gross() -> None:
    catalog = cloned_catalog("nibelis")
    rubric = find_record(catalog, "rubrics", "rubric_code", "COMPTEURS_INFO_SYN")
    rubric["affects_gross"] = True
    report = report_for("nibelis", catalog)
    assert_issue(report, "nibelis_informational_cannot_affect_gross")


def test_reject_nibelis_counter_information_with_non_informational_impact() -> None:
    catalog = cloned_catalog("nibelis")
    rubric = find_record(catalog, "rubrics", "rubric_code", "REPOS_COMP_SYN")
    rubric["gross_impact"] = "positive"
    report = report_for("nibelis", catalog)
    assert_issue(report, "nibelis_counter_information_must_be_informational")


def test_reject_nibelis_hidden_rubric_described_as_visible() -> None:
    catalog = cloned_catalog("nibelis")
    rubric = find_record(catalog, "rubrics", "rubric_code", "REG_PAIE_SYN")
    rubric["appears_on_payslip"] = False
    rubric["notes"] = ["Cette rubrique est visible sur le bulletin fictif"]
    report = report_for("nibelis", catalog)
    assert_issue(report, "nibelis_hidden_rubric_described_as_visible")


def test_reject_nibelis_payslip_rubric_without_anonymization_guard() -> None:
    catalog = cloned_catalog("nibelis")
    catalog["rubrics"][0]["anonymization_required"] = False
    report = report_for("nibelis", catalog)
    assert_issue(report, "nibelis_anonymization_required")


def test_calculation_allowed_requires_source_date_and_human_validation() -> None:
    catalog = cloned_catalog("parameters")
    catalog["fixture_type"] = "private_local"
    record = catalog["parameters"][0]
    record["calculation_allowed"] = True
    record["synthetic_only"] = False
    record["source_layer"] = "synthetic_fixture"
    record["source_document"] = ""
    record["source_reference"] = None
    record["effective_date"] = None
    record["validation_status"] = "to_verify"
    record["confidence"] = "medium"
    record["human_validation"]["status"] = "pending"
    report = report_for("parameters", catalog)
    assert_issue(report, "calculation_without_source")
    assert_issue(report, "calculation_with_untrusted_source_layer")
    assert_issue(report, "calculation_without_effective_date")
    assert_issue(report, "calculation_without_human_validation")
    assert_issue(report, "calculation_without_high_confidence")
    assert_issue(report, "calculation_without_validated_human_status")


def test_private_validated_parameter_can_pass_calculation_gate() -> None:
    catalog = cloned_catalog("parameters")
    catalog["fixture_type"] = "private_local"
    record = catalog["parameters"][0]
    record["calculation_allowed"] = True
    record["synthetic_only"] = False
    record["source_layer"] = "accord_entreprise"
    record["source_document"] = "Document synthetique de test valide"
    record["source_reference"] = "test:source:1"
    record["effective_date"] = "2026-01-01"
    record["validation_status"] = "human_validated"
    record["confidence"] = "high"
    record["human_validation"]["status"] = "validated"
    record["human_validation"]["validator"] = "validateur synthetique"
    record["human_validation"]["validated_at"] = "2026-01-01"
    report = report_for("parameters", catalog)
    assert report["valid"], report


def test_reject_nested_unknown_field() -> None:
    catalog = cloned_catalog("parameters")
    catalog["parameters"][0]["human_validation"]["unexpected_field"] = True
    report = report_for("parameters", catalog)
    assert_issue(report, "unknown_field")


def test_detect_email_in_fixture() -> None:
    catalog = cloned_catalog("nibelis")
    catalog["rubrics"][0]["notes"] = ["Contact test thierry@example.com"]
    report = report_for("nibelis", catalog)
    assert_issue(report, "sensitive_data_detected")


def test_detect_phone_number_in_fixture() -> None:
    catalog = cloned_catalog("kelio")
    catalog["counters"][0]["notes"] = ["Numero fictif interdit 06 12 34 56 78"]
    report = report_for("kelio", catalog)
    assert_issue(report, "sensitive_data_detected")


def test_detect_iban_in_fixture() -> None:
    catalog = cloned_catalog("parameters")
    catalog["parameters"][0]["notes"] = ["IBAN interdit FR76 3000 6000 0112 3456 7890 189"]
    report = report_for("parameters", catalog)
    assert_issue(report, "sensitive_data_detected")


def test_detect_social_security_number_in_fixture() -> None:
    catalog = cloned_catalog("parameters")
    catalog["parameters"][0]["notes"] = ["NIR interdit 1 84 12 57 123 456 78"]
    report = report_for("parameters", catalog)
    assert_issue(report, "sensitive_data_detected")


def test_detect_matricule_in_fixture() -> None:
    catalog = cloned_catalog("kelio")
    catalog["counters"][0]["notes"] = ["matricule salarie interdit dans une fixture"]
    report = report_for("kelio", catalog)
    assert_issue(report, "sensitive_data_detected")


def test_distinguishes_source_calculated_and_controlled_data() -> None:
    nibelis = cloned_catalog("nibelis")
    kelio = cloned_catalog("kelio")
    parameters = cloned_catalog("parameters")
    assert nibelis["rubrics"][0]["data_role"] == "controlled_data"
    assert kelio["counters"][0]["data_role"] == "source_data"
    assert parameters["parameters"][0]["data_role"] == "source_data"
    for kind, catalog in [("nibelis", nibelis), ("kelio", kelio), ("parameters", parameters)]:
        report = report_for(kind, catalog)
        assert_no_issue(report, "missing_required_field")


def run_all() -> None:
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print(f"OK {name}")


if __name__ == "__main__":
    run_all()
