#!/usr/bin/env python
"""Validate structured payroll and leave rules for CFDT Nexus.

This validator is intentionally local and deterministic. It does not connect
to the Nexus router and it does not calculate payroll amounts.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = REPO_ROOT / "database" / "payroll" / "payroll-rule.schema.json"
DEFAULT_CATALOG_PATH = REPO_ROOT / "database" / "payroll" / "ineos-sarralbe-payroll-rules-v1.json"

INTERNAL_SOURCE_LAYERS = {"accord_entreprise", "memoire_entreprise"}
SPECIFIC_WORK_TOPICS = {"5x8", "poste_continu", "gn", "polyolefines", "roulement"}
SPECIFIC_WORK_SCHEDULES = {"5x8", "poste_continu", "gn", "polyolefines", "roulement"}
RATE_PATTERN = re.compile(
    r"(?<!\w)\d+(?:[,.]\d+)?\s*(?:%|eur(?:o|os)?(?:/km)?|€(?:/km)?|h|heure|heures|km)(?!\w)",
    re.IGNORECASE,
)
NON_EMPTY_REQUIRED_FIELDS = {
    "rule_id",
    "title",
    "description",
    "source_layer",
    "document_type",
    "source_document",
    "source_chunk_id",
    "status",
    "confidentiality",
    "confidence",
    "site",
    "calculation_formula",
    "benefit_or_obligation",
    "legal_priority",
    "validation_status",
}
DATE_FIELDS = {"source_date", "effective_date", "end_date"}
SUPPORTED_SCHEMA_KEYS = {
    "$defs",
    "$id",
    "$ref",
    "$schema",
    "additionalProperties",
    "enum",
    "items",
    "properties",
    "required",
    "title",
    "type",
}


@dataclass
class ValidationIssue:
    code: str
    message: str
    field: str | None = None

    def as_dict(self) -> dict[str, str]:
        value = {"code": self.code, "message": self.message}
        if self.field:
            value["field"] = self.field
        return value


@dataclass
class ValidationResult:
    rule_id: str
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "valid": self.valid,
            "errors": [issue.as_dict() for issue in self.errors],
            "warnings": [issue.as_dict() for issue in self.warnings],
        }


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_schema(path: Path = DEFAULT_SCHEMA_PATH) -> dict[str, Any]:
    schema = load_json(path)
    if not isinstance(schema, dict) or "$defs" not in schema or "PayrollRule" not in schema["$defs"]:
        raise ValueError("Invalid payroll rule schema: missing $defs.PayrollRule")
    return schema


def load_catalog(path: Path = DEFAULT_CATALOG_PATH) -> dict[str, Any]:
    catalog = load_json(path)
    if not isinstance(catalog, dict) or not isinstance(catalog.get("rules"), list):
        raise ValueError("Invalid payroll rule catalog: missing rules list")
    return catalog


def enum_values(schema: dict[str, Any], field_name: str) -> set[str]:
    rule_schema = schema["$defs"]["PayrollRule"]
    definition = rule_schema["properties"].get(field_name, {})
    if "enum" in definition:
        return set(definition["enum"])
    if definition.get("type") == "array":
        return set(definition.get("items", {}).get("enum", []))
    return set()


def issue_field(path: str) -> str:
    return path[2:] if path.startswith("$.") else path


def schema_type_matches(value: Any, expected_type: str) -> bool:
    if expected_type == "null":
        return value is None
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    return False


def expected_type_label(type_definition: Any) -> str:
    if isinstance(type_definition, list):
        return " or ".join(str(item) for item in type_definition)
    return str(type_definition)


def resolve_ref(schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"Unsupported schema reference: {ref}")
    current: Any = schema
    for part in ref[2:].split("/"):
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"Unresolved schema reference: {ref}")
        current = current[part]
    if not isinstance(current, dict):
        raise ValueError(f"Schema reference does not resolve to an object: {ref}")
    return current


def validate_schema_node(value: Any, node: dict[str, Any], root_schema: dict[str, Any], path: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if "$ref" in node:
        return validate_schema_node(value, resolve_ref(root_schema, str(node["$ref"])), root_schema, path)

    type_definition = node.get("type")
    if type_definition is not None:
        expected_types = type_definition if isinstance(type_definition, list) else [type_definition]
        if not any(schema_type_matches(value, str(expected_type)) for expected_type in expected_types):
            issues.append(
                ValidationIssue(
                    "invalid_type",
                    f"Invalid type at {issue_field(path)}: expected {expected_type_label(type_definition)}.",
                    issue_field(path),
                )
            )
            return issues

    if "enum" in node and value not in node["enum"]:
        issues.append(
            ValidationIssue(
                "invalid_enum",
                f"Invalid enum value at {issue_field(path)}: {value!r}.",
                issue_field(path),
            )
        )

    if isinstance(value, dict):
        properties = node.get("properties", {})
        required = node.get("required", [])
        for field_name in required:
            if field_name not in value:
                issues.append(
                    ValidationIssue(
                        "missing_required_field",
                        f"Missing required field: {issue_field(path + '.' + field_name)}",
                        issue_field(path + "." + field_name),
                    )
                )
        if node.get("additionalProperties") is False:
            for field_name in value:
                if field_name not in properties:
                    issues.append(
                        ValidationIssue(
                            "unknown_field",
                            f"Unknown field is not allowed: {issue_field(path + '.' + field_name)}",
                            issue_field(path + "." + field_name),
                        )
                    )
        for field_name, child_schema in properties.items():
            if field_name in value:
                issues.extend(validate_schema_node(value[field_name], child_schema, root_schema, path + "." + field_name))

    if isinstance(value, list) and "items" in node:
        for index, item in enumerate(value):
            issues.extend(validate_schema_node(item, node["items"], root_schema, f"{path}[{index}]"))

    return issues


def walk_schema_nodes(node: Any, root_schema: dict[str, Any], path: str = "$") -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(node, dict):
        return issues
    for key in node:
        if key not in SUPPORTED_SCHEMA_KEYS:
            issues.append(ValidationIssue("unsupported_schema_keyword", f"Unsupported schema keyword: {key}", issue_field(path)))
    if "$ref" in node:
        try:
            resolve_ref(root_schema, str(node["$ref"]))
        except ValueError as exc:
            issues.append(ValidationIssue("invalid_schema_ref", str(exc), issue_field(path)))
    if "properties" in node:
        if not isinstance(node["properties"], dict):
            issues.append(ValidationIssue("invalid_schema_properties", "Schema properties must be an object.", issue_field(path)))
        else:
            for field_name, child in node["properties"].items():
                issues.extend(walk_schema_nodes(child, root_schema, path + "." + field_name))
    if "items" in node:
        issues.extend(walk_schema_nodes(node["items"], root_schema, path + "[]"))
    if "$defs" in node:
        if not isinstance(node["$defs"], dict):
            issues.append(ValidationIssue("invalid_schema_defs", "Schema $defs must be an object.", issue_field(path)))
        else:
            for def_name, child in node["$defs"].items():
                issues.extend(walk_schema_nodes(child, root_schema, path + ".$defs." + def_name))
    return issues


def validate_schema_structure(schema: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(schema, dict):
        return [ValidationIssue("invalid_schema", "Schema root must be an object.", "$")]
    if schema.get("type") != "object":
        issues.append(ValidationIssue("invalid_schema_root_type", "Schema root must declare type object.", "type"))
    if "$defs" not in schema or "PayrollRule" not in schema.get("$defs", {}):
        issues.append(ValidationIssue("invalid_schema_defs", "Schema must define $defs.PayrollRule.", "$defs"))
    issues.extend(walk_schema_nodes(schema, schema))
    return issues


def is_empty(value: Any) -> bool:
    return value is None or value == "" or value == []


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def normalize_text(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(normalize_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(normalize_text(item) for item in value.values())
    return str(value or "").lower()


def has_sourced_rate(formula: dict[str, Any]) -> bool:
    source_refs = formula.get("source_refs") or []
    values = formula.get("sourced_values") or []
    if source_refs:
        return True
    for item in values:
        if not isinstance(item, dict):
            continue
        if RATE_PATTERN.search(str(item.get("value", ""))) and item.get("source"):
            return True
    return False


def validate_schema_conformance(rule: dict[str, Any], schema: dict[str, Any], result: ValidationResult) -> None:
    rule_schema = schema["$defs"]["PayrollRule"]
    result.errors.extend(validate_schema_node(rule, rule_schema, schema, "$"))
    for field_name in NON_EMPTY_REQUIRED_FIELDS:
        if field_name in rule and is_empty(rule.get(field_name)):
            result.errors.append(ValidationIssue("empty_required_field", f"Required field is empty: {field_name}", field_name))
    for field_name in DATE_FIELDS:
        value = rule.get(field_name)
        if value is not None and isinstance(value, str) and parse_date(value) is None:
            result.errors.append(
                ValidationIssue("invalid_date", f"Invalid ISO date for {field_name}: {value}", field_name)
            )
    effective_date = parse_date(rule.get("effective_date"))
    end_date = parse_date(rule.get("end_date"))
    if effective_date and end_date and effective_date > end_date:
        result.errors.append(
            ValidationIssue(
                "effective_date_after_end_date",
                "effective_date must be earlier than or equal to end_date.",
                "effective_date",
            )
        )


def validate_business_rules(
    rule: dict[str, Any],
    schema: dict[str, Any],
    all_rules: list[dict[str, Any]] | None = None,
    today: date | None = None,
) -> ValidationResult:
    result = ValidationResult(rule_id=str(rule.get("rule_id", "UNKNOWN")))
    validate_schema_conformance(rule, schema, result)

    source_layer = str(rule.get("source_layer", ""))
    document_type = str(rule.get("document_type", ""))
    source_document = normalize_text(rule.get("source_document", ""))
    legal_priority = str(rule.get("legal_priority", ""))
    status = str(rule.get("status", ""))
    calculation_allowed = rule.get("calculation_allowed") is True
    required_variables = rule.get("required_variables") if isinstance(rule.get("required_variables"), list) else []
    formula = rule.get("calculation_formula") if isinstance(rule.get("calculation_formula"), dict) else {}
    work_topics = set(rule.get("work_time_topic") if isinstance(rule.get("work_time_topic"), list) else [])
    work_schedules = set(rule.get("work_schedule") if isinstance(rule.get("work_schedule"), list) else [])
    populations = set(rule.get("employee_population") if isinstance(rule.get("employee_population"), list) else [])

    if not rule.get("source_layer") or not rule.get("source_document"):
        result.errors.append(ValidationIssue("missing_source", "A payroll rule must cite a source layer and a source document."))

    if source_layer in INTERNAL_SOURCE_LAYERS and not rule.get("source_page") and not rule.get("source_chunk_id"):
        result.errors.append(
            ValidationIssue(
                "missing_internal_trace",
                "Internal sources must provide a page or a documentary trace before use.",
                "source_page",
            )
        )

    if calculation_allowed and not required_variables:
        result.errors.append(
            ValidationIssue(
                "calculation_without_variables",
                "A calculable rule must declare the required variables.",
                "required_variables",
            )
        )

    if source_layer == "memoire_entreprise" and calculation_allowed:
        result.errors.append(
            ValidationIssue(
                "memory_source_cannot_calculate",
                "A company memory source cannot authorize payroll calculation.",
                "calculation_allowed",
            )
        )

    if source_layer == "memoire_entreprise" and legal_priority != "memory_only":
        result.errors.append(
            ValidationIssue(
                "memory_source_must_be_memory_only",
                "A company memory source cannot be an opposable or interpretative source.",
                "legal_priority",
            )
        )

    if source_layer == "memoire_entreprise" and not rule.get("historical_only"):
        result.errors.append(
            ValidationIssue(
                "memory_source_must_be_historical",
                "A company memory source must remain historical_only.",
                "historical_only",
            )
        )

    if document_type == "pv_cse":
        if source_layer != "memoire_entreprise":
            result.errors.append(
                ValidationIssue(
                    "pv_cse_wrong_source_layer",
                    "A PV CSE must use source_layer memoire_entreprise.",
                    "source_layer",
                )
            )
        if rule.get("historical_only") is not True:
            result.errors.append(
                ValidationIssue(
                    "pv_cse_must_be_historical",
                    "A PV CSE must be historical_only.",
                    "historical_only",
                )
            )
        if rule.get("calculation_allowed") is not False:
            result.errors.append(
                ValidationIssue(
                    "pv_cse_cannot_calculate",
                    "A PV CSE cannot authorize a payroll calculation.",
                    "calculation_allowed",
                )
            )
        if legal_priority != "memory_only":
            result.errors.append(
                ValidationIssue(
                    "pv_cse_wrong_legal_priority",
                    "A PV CSE must use legal_priority memory_only.",
                    "legal_priority",
                )
            )

    if status == "active" and parse_date(rule.get("end_date")) and (today or date.today()) > parse_date(rule.get("end_date")):
        result.warnings.append(
            ValidationIssue(
                "active_rule_expired",
                "The rule is active but its end_date is already passed.",
                "end_date",
            )
        )

    if status == "active" and rule.get("superseded_by"):
        result.warnings.append(
            ValidationIssue(
                "active_rule_superseded",
                "The rule is active but declares a superseded_by reference.",
                "superseded_by",
            )
        )

    if (work_topics & SPECIFIC_WORK_TOPICS or work_schedules & SPECIFIC_WORK_SCHEDULES) and not populations:
        result.errors.append(
            ValidationIssue(
                "specific_rule_without_population",
                "A specific 5x8/GN/Polyolefines rule must declare its employee population.",
                "employee_population",
            )
        )

    expression = normalize_text(formula.get("expression", ""))
    if RATE_PATTERN.search(expression) and not has_sourced_rate(formula):
        result.errors.append(
            ValidationIssue(
                "unsourced_rate_in_formula",
                "A formula containing a rate or amount must cite the source for that value.",
                "calculation_formula",
            )
        )

    for item in formula.get("sourced_values") or []:
        if not isinstance(item, dict):
            continue
        if RATE_PATTERN.search(str(item.get("value", ""))) and not item.get("source"):
            result.errors.append(
                ValidationIssue(
                    "unsourced_formula_value",
                    "A sourced formula value contains a rate or amount without a source.",
                    "calculation_formula.sourced_values",
                )
            )

    if all_rules:
        superseding_ids = {
            superseded
            for other in all_rules
            for superseded in (other.get("supersedes") or [])
            if other.get("rule_id") != rule.get("rule_id")
        }
        if rule.get("rule_id") in superseding_ids and status == "active":
            result.warnings.append(
                ValidationIssue(
                    "potential_newer_version_conflict",
                    "Another rule declares this rule as superseded; status should be reviewed.",
                    "status",
                )
            )

    return result


def validate_rule(
    rule: dict[str, Any],
    schema: dict[str, Any] | None = None,
    all_rules: list[dict[str, Any]] | None = None,
    today: date | None = None,
) -> ValidationResult:
    return validate_business_rules(rule, schema or load_schema(), all_rules=all_rules, today=today)


def detect_supersedes_cycles(rules_by_id: dict[str, dict[str, Any]]) -> set[str]:
    graph: dict[str, list[str]] = {}
    for rule_id, rule in rules_by_id.items():
        refs = rule.get("supersedes")
        graph[rule_id] = [ref for ref in refs if isinstance(ref, str) and ref in rules_by_id] if isinstance(refs, list) else []

    cycle_nodes: set[str] = set()
    visited: set[str] = set()
    visiting: list[str] = []

    def visit(rule_id: str) -> None:
        if rule_id in visiting:
            cycle_nodes.update(visiting[visiting.index(rule_id) :])
            return
        if rule_id in visited:
            return
        visiting.append(rule_id)
        for target in graph.get(rule_id, []):
            visit(target)
        visiting.pop()
        visited.add(rule_id)

    for rule_id in graph:
        visit(rule_id)
    return cycle_nodes


def validate_catalog(
    catalog: dict[str, Any],
    schema: dict[str, Any] | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    schema = schema or load_schema()
    catalog_errors = validate_schema_node(catalog, schema, schema, "$")
    rules = catalog.get("rules") if isinstance(catalog, dict) else []
    if not isinstance(rules, list):
        rules = []
    result_objects: list[ValidationResult] = []
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            result_objects.append(
                ValidationResult(
                    rule_id=f"INVALID_RULE_{index}",
                    errors=[
                        ValidationIssue(
                            "invalid_type",
                            f"Catalog rule at index {index} must be an object.",
                            f"rules[{index}]",
                        )
                    ],
                )
            )
            continue
        result_objects.append(validate_rule(rule, schema=schema, all_rules=rules, today=today))

    rule_ids = [rule.get("rule_id") for rule in rules if isinstance(rule, dict)]
    duplicate_ids = sorted({rule_id for rule_id in rule_ids if isinstance(rule_id, str) and rule_ids.count(rule_id) > 1})
    if duplicate_ids:
        for result in result_objects:
            if result.rule_id in duplicate_ids:
                result.errors.append(
                    ValidationIssue("duplicate_rule_id", f"Duplicate rule_id: {result.rule_id}", "rule_id")
                )

    results_by_id: dict[str, ValidationResult] = {
        result.rule_id: result for result in result_objects if result.rule_id not in duplicate_ids
    }
    rules_by_id: dict[str, dict[str, Any]] = {
        str(rule.get("rule_id")): rule
        for rule in rules
        if isinstance(rule, dict) and rule.get("rule_id") not in duplicate_ids
    }
    for rule, result in zip(rules, result_objects):
        if not isinstance(rule, dict):
            continue
        rule_id = str(rule.get("rule_id", "UNKNOWN"))
        for field_name, reciprocal_field in [("supersedes", "superseded_by"), ("superseded_by", "supersedes")]:
            refs = rule.get(field_name)
            if not isinstance(refs, list):
                continue
            seen: set[str] = set()
            for ref in refs:
                if not isinstance(ref, str):
                    continue
                if ref == rule_id:
                    result.errors.append(
                        ValidationIssue("self_reference", f"{field_name} cannot reference the same rule_id.", field_name)
                    )
                if ref in seen:
                    result.errors.append(
                        ValidationIssue("duplicate_reference", f"Duplicate reference in {field_name}: {ref}", field_name)
                    )
                seen.add(ref)
                if ref not in results_by_id:
                    result.errors.append(
                        ValidationIssue("unknown_rule_reference", f"Unknown rule_id in {field_name}: {ref}", field_name)
                    )
                    continue
                reciprocal_refs = rules_by_id.get(ref, {}).get(reciprocal_field)
                if isinstance(reciprocal_refs, list) and reciprocal_refs and rule_id not in reciprocal_refs:
                    result.errors.append(
                        ValidationIssue(
                            "inconsistent_reciprocal_reference",
                            f"{field_name} references {ref}, but {reciprocal_field} does not reference {rule_id}.",
                            field_name,
                        )
                    )

    cycle_nodes = detect_supersedes_cycles(rules_by_id)
    for rule_id in cycle_nodes:
        result = results_by_id.get(rule_id)
        if result:
            result.errors.append(
                ValidationIssue(
                    "supersedes_cycle",
                    "The supersedes graph contains a cycle involving this rule.",
                    "supersedes",
                )
            )

    results = [result.as_dict() for result in result_objects]
    return {
        "rules_count": len(rules),
        "valid": not catalog_errors and all(not result.errors for result in result_objects),
        "errors_count": len(catalog_errors) + sum(len(result["errors"]) for result in results),
        "warnings_count": sum(len(result["warnings"]) for result in results),
        "duplicate_rule_ids": duplicate_ids,
        "catalog_errors": [issue.as_dict() for issue in catalog_errors],
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate CFDT Nexus payroll rules.")
    parser.add_argument("command", choices=["validate-schema", "validate-catalog"])
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG_PATH))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA_PATH))
    args = parser.parse_args(argv)

    schema = load_schema(Path(args.schema))
    if args.command == "validate-schema":
        issues = validate_schema_structure(schema)
        report = {
            "schema": str(Path(args.schema)),
            "valid": not issues,
            "errors_count": len(issues),
            "errors": [issue.as_dict() for issue in issues],
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if not issues else 1

    catalog = load_catalog(Path(args.catalog))
    report = validate_catalog(catalog, schema=schema)
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2, ensure_ascii=False))
    if not report["valid"]:
        print(json.dumps(report["results"], indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
