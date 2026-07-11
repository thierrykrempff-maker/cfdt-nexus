#!/usr/bin/env python
"""Local tests for the PayrollRule validator.

The tests use synthetic rules only. They do not load private documents and do
not require network access.
"""

from __future__ import annotations

import copy
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from automation.payroll import payroll_rule_validator as validator  # noqa: E402


SCHEMA = validator.load_schema()


def valid_rule() -> dict[str, object]:
    return {
        "rule_id": "TEST_VALID_RULE",
        "title": "Regle de test valide",
        "description": "Regle synthetique destinee aux tests du validateur.",
        "source_layer": "accord_entreprise",
        "document_type": "accord",
        "source_document": "Document de test",
        "source_page": 1,
        "source_chunk_id": "test:chunk:1",
        "source_date": "2026-01-01",
        "effective_date": "2026-01-01",
        "end_date": None,
        "supersedes": [],
        "superseded_by": [],
        "status": "to_verify",
        "historical_only": False,
        "confidentiality": "internal",
        "confidence": "medium",
        "payroll_topic": ["prime_poste"],
        "leave_topic": [],
        "work_time_topic": ["5x8"],
        "employee_population": ["personnel_poste"],
        "employment_category": ["non_cadres"],
        "work_schedule": ["5x8"],
        "site": "INEOS Sarralbe",
        "conditions": ["Condition de test"],
        "exclusions": [],
        "required_variables": ["variable_test"],
        "calculation_formula": {
            "expression": "Calcul desactive dans le lot 1.",
            "source_refs": ["test:chunk:1"],
            "sourced_values": [],
            "limitations": ["Test uniquement"],
        },
        "calculation_allowed": False,
        "benefit_or_obligation": "droit_salarie",
        "payroll_lines_to_check": ["ligne de test"],
        "kelio_counters": ["compteur_test"],
        "legal_priority": "to_verify",
        "notes": ["Regle synthetique"],
        "validation_status": "human_review_required",
    }


def assert_error(result: validator.ValidationResult, code: str) -> None:
    assert any(issue.code == code for issue in result.errors), result.as_dict()


def assert_warning(result: validator.ValidationResult, code: str) -> None:
    assert any(issue.code == code for issue in result.warnings), result.as_dict()


def catalog_with(*rules: dict[str, object]) -> dict[str, object]:
    return {
        "catalog_id": "test-catalog",
        "version": "test",
        "scope": "tests",
        "rules": list(rules),
    }


def assert_catalog_error(report: dict[str, object], rule_id: str, code: str) -> None:
    for result in report["results"]:
        if result["rule_id"] == rule_id:
            assert any(issue["code"] == code for issue in result["errors"]), result
            return
    raise AssertionError(f"rule_id not found in report: {rule_id}")


def assert_catalog_root_error(report: dict[str, object], code: str) -> None:
    assert any(issue["code"] == code for issue in report["catalog_errors"]), report


def test_valid_rule() -> None:
    result = validator.validate_rule(valid_rule(), schema=SCHEMA)
    assert result.valid, result.as_dict()


def test_reject_rule_without_source() -> None:
    rule = valid_rule()
    rule["source_document"] = ""
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "empty_required_field")
    assert_error(result, "missing_source")


def test_reject_boolean_as_string() -> None:
    rule = valid_rule()
    rule["calculation_allowed"] = "false"
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "invalid_type")


def test_reject_array_as_string() -> None:
    rule = valid_rule()
    rule["employee_population"] = "personnel_poste"
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "invalid_type")


def test_reject_unknown_field() -> None:
    rule = valid_rule()
    rule["unknown_field"] = "not allowed"
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "unknown_field")


def test_reject_invalid_date() -> None:
    rule = valid_rule()
    rule["effective_date"] = "not-a-date"
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "invalid_date")


def test_reject_effective_date_after_end_date() -> None:
    rule = valid_rule()
    rule["effective_date"] = "2026-01-02"
    rule["end_date"] = "2026-01-01"
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "effective_date_after_end_date")


def test_reject_invalid_source_layer() -> None:
    rule = valid_rule()
    rule["source_layer"] = "source_inconnue"
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "invalid_enum")


def test_reject_incomplete_formula_object() -> None:
    rule = valid_rule()
    rule["calculation_formula"] = {"expression": "Calcul incomplet."}
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "missing_required_field")


def test_reject_incomplete_nested_formula_value() -> None:
    rule = valid_rule()
    rule["calculation_formula"] = {
        "expression": "Montant = base x 40%",
        "source_refs": ["test:chunk:1"],
        "sourced_values": [{"label": "taux", "value": "40%", "status": "to_verify"}],
        "limitations": [],
    }
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "missing_required_field")


def test_accept_well_classified_pv_cse() -> None:
    rule = valid_rule()
    rule["rule_id"] = "TEST_PV_CSE_OK"
    rule["source_layer"] = "memoire_entreprise"
    rule["document_type"] = "pv_cse"
    rule["source_document"] = "PV CSE test"
    rule["historical_only"] = True
    rule["calculation_allowed"] = False
    rule["legal_priority"] = "memory_only"
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert result.valid, result.as_dict()


def test_reject_pv_cse_wrong_source_layer() -> None:
    rule = valid_rule()
    rule["document_type"] = "pv_cse"
    rule["source_document"] = "PV CSE test"
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "pv_cse_wrong_source_layer")


def test_reject_pv_cse_not_historical() -> None:
    rule = valid_rule()
    rule["source_layer"] = "memoire_entreprise"
    rule["document_type"] = "pv_cse"
    rule["source_document"] = "PV CSE test"
    rule["historical_only"] = False
    rule["legal_priority"] = "memory_only"
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "pv_cse_must_be_historical")


def test_reject_pv_cse_calculable() -> None:
    rule = valid_rule()
    rule["source_layer"] = "memoire_entreprise"
    rule["document_type"] = "pv_cse"
    rule["source_document"] = "PV CSE test"
    rule["historical_only"] = True
    rule["calculation_allowed"] = True
    rule["legal_priority"] = "memory_only"
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "memory_source_cannot_calculate")
    assert_error(result, "pv_cse_cannot_calculate")


def test_reject_pv_cse_wrong_legal_priority() -> None:
    rule = valid_rule()
    rule["source_layer"] = "memoire_entreprise"
    rule["document_type"] = "pv_cse"
    rule["source_document"] = "PV CSE test"
    rule["historical_only"] = True
    rule["legal_priority"] = "to_verify"
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "pv_cse_wrong_legal_priority")


def test_reject_unsourced_rate() -> None:
    rule = valid_rule()
    rule["calculation_formula"] = {
        "expression": "Montant = base x 40%",
        "source_refs": [],
        "sourced_values": [],
        "limitations": [],
    }
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "unsourced_rate_in_formula")


def test_signal_expired_active_rule() -> None:
    rule = valid_rule()
    rule["status"] = "active"
    rule["effective_date"] = "2025-01-01"
    rule["end_date"] = "2025-12-31"
    result = validator.validate_rule(rule, schema=SCHEMA, today=date(2026, 7, 11))
    assert result.valid, result.as_dict()
    assert_warning(result, "active_rule_expired")


def test_signal_superseded_active_rule() -> None:
    rule = valid_rule()
    rule["status"] = "active"
    rule["superseded_by"] = ["TEST_NEW_RULE"]
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert result.valid, result.as_dict()
    assert_warning(result, "active_rule_superseded")


def test_reject_specific_5x8_without_population() -> None:
    rule = valid_rule()
    rule["employee_population"] = []
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "specific_rule_without_population")


def test_reject_calculation_without_variables() -> None:
    rule = valid_rule()
    rule["calculation_allowed"] = True
    rule["required_variables"] = []
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "calculation_without_variables")


def test_memory_rule_kept_historical_only() -> None:
    rule = valid_rule()
    rule["source_layer"] = "memoire_entreprise"
    rule["document_type"] = "note_rh"
    rule["historical_only"] = True
    rule["calculation_allowed"] = False
    rule["legal_priority"] = "memory_only"
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert result.valid, result.as_dict()


def test_catalog_loads_and_validates() -> None:
    catalog = validator.load_catalog()
    report = validator.validate_catalog(catalog, schema=SCHEMA)
    assert report["rules_count"] >= 20
    assert report["valid"], report


def test_reject_unknown_catalog_root_field() -> None:
    rule = valid_rule()
    report = validator.validate_catalog(catalog_with(rule) | {"unexpected_field": True}, schema=SCHEMA)
    assert_catalog_root_error(report, "unknown_field")


def test_rule_ids_are_unique() -> None:
    catalog = validator.load_catalog()
    rule_ids = [rule["rule_id"] for rule in catalog["rules"]]
    assert len(rule_ids) == len(set(rule_ids))


def test_all_catalog_rules_match_schema() -> None:
    catalog = validator.load_catalog()
    required = set(SCHEMA["$defs"]["PayrollRule"]["required"])
    for rule in catalog["rules"]:
        assert required <= set(rule), rule.get("rule_id")
        result = validator.validate_rule(rule, schema=SCHEMA)
        assert result.valid, result.as_dict()


def test_detect_newer_version_conflict() -> None:
    old_rule = valid_rule()
    old_rule["rule_id"] = "OLD_RULE"
    old_rule["status"] = "active"
    new_rule = copy.deepcopy(valid_rule())
    new_rule["rule_id"] = "NEW_RULE"
    new_rule["supersedes"] = ["OLD_RULE"]
    result = validator.validate_rule(old_rule, schema=SCHEMA, all_rules=[old_rule, new_rule])
    assert_warning(result, "potential_newer_version_conflict")


def test_reject_invalid_supersedes_type() -> None:
    rule = valid_rule()
    rule["supersedes"] = ["KNOWN_RULE", 12]
    result = validator.validate_rule(rule, schema=SCHEMA)
    assert_error(result, "invalid_type")


def test_reject_unknown_supersedes_reference() -> None:
    rule = valid_rule()
    rule["supersedes"] = ["UNKNOWN_RULE"]
    report = validator.validate_catalog(catalog_with(rule), schema=SCHEMA)
    assert_catalog_error(report, "TEST_VALID_RULE", "unknown_rule_reference")


def test_reject_self_reference() -> None:
    rule = valid_rule()
    rule["supersedes"] = ["TEST_VALID_RULE"]
    report = validator.validate_catalog(catalog_with(rule), schema=SCHEMA)
    assert_catalog_error(report, "TEST_VALID_RULE", "self_reference")


def test_reject_duplicate_reference() -> None:
    rule = valid_rule()
    target = valid_rule()
    target["rule_id"] = "TARGET_RULE"
    rule["supersedes"] = ["TARGET_RULE", "TARGET_RULE"]
    report = validator.validate_catalog(catalog_with(rule, target), schema=SCHEMA)
    assert_catalog_error(report, "TEST_VALID_RULE", "duplicate_reference")


def test_reject_inconsistent_reciprocal_reference() -> None:
    old_rule = valid_rule()
    old_rule["rule_id"] = "OLD_RULE"
    old_rule["superseded_by"] = ["OTHER_RULE"]
    new_rule = valid_rule()
    new_rule["rule_id"] = "NEW_RULE"
    new_rule["supersedes"] = ["OLD_RULE"]
    report = validator.validate_catalog(catalog_with(old_rule, new_rule), schema=SCHEMA)
    assert_catalog_error(report, "NEW_RULE", "inconsistent_reciprocal_reference")


def test_reject_two_rule_supersedes_cycle() -> None:
    first = valid_rule()
    first["rule_id"] = "RULE_A"
    first["supersedes"] = ["RULE_B"]
    second = valid_rule()
    second["rule_id"] = "RULE_B"
    second["supersedes"] = ["RULE_A"]
    report = validator.validate_catalog(catalog_with(first, second), schema=SCHEMA)
    assert_catalog_error(report, "RULE_A", "supersedes_cycle")
    assert_catalog_error(report, "RULE_B", "supersedes_cycle")


def test_reject_three_rule_supersedes_cycle() -> None:
    first = valid_rule()
    first["rule_id"] = "RULE_A"
    first["supersedes"] = ["RULE_B"]
    second = valid_rule()
    second["rule_id"] = "RULE_B"
    second["supersedes"] = ["RULE_C"]
    third = valid_rule()
    third["rule_id"] = "RULE_C"
    third["supersedes"] = ["RULE_A"]
    report = validator.validate_catalog(catalog_with(first, second, third), schema=SCHEMA)
    assert_catalog_error(report, "RULE_A", "supersedes_cycle")
    assert_catalog_error(report, "RULE_B", "supersedes_cycle")
    assert_catalog_error(report, "RULE_C", "supersedes_cycle")


def test_accept_valid_supersedes_chain() -> None:
    newest = valid_rule()
    newest["rule_id"] = "RULE_A"
    newest["supersedes"] = ["RULE_B"]
    middle = valid_rule()
    middle["rule_id"] = "RULE_B"
    middle["supersedes"] = ["RULE_C"]
    oldest = valid_rule()
    oldest["rule_id"] = "RULE_C"
    report = validator.validate_catalog(catalog_with(newest, middle, oldest), schema=SCHEMA)
    assert report["valid"], report


def test_reject_duplicate_rule_id() -> None:
    first = valid_rule()
    second = valid_rule()
    report = validator.validate_catalog(catalog_with(first, second), schema=SCHEMA)
    assert_catalog_error(report, "TEST_VALID_RULE", "duplicate_rule_id")


def run_all() -> None:
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print(f"OK {name}")


if __name__ == "__main__":
    run_all()
