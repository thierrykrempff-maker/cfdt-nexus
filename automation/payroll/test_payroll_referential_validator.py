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


def test_all_example_referentials_validate() -> None:
    report = validator.validate_all()
    assert report["valid"], report
    assert report["reports"]["nibelis"]["records_count"] == 3
    assert report["reports"]["kelio"]["records_count"] == 3
    assert report["reports"]["parameters"]["records_count"] == 3


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
