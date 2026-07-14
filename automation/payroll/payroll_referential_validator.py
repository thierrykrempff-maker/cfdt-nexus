#!/usr/bin/env python
"""Validate CFDT Nexus payroll referentials.

LOT 4A stays local and deterministic. It validates only schemas and synthetic
fixtures for Nibelis rubrics, Kelio counters and payroll parameters. It does
not connect to Nibelis, Kelio, the Nexus router or any external API.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from automation.payroll import payroll_rule_validator as rule_validator  # noqa: E402


REFERENTIAL_DIR = REPO_ROOT / "database" / "payroll" / "referentials"

REFERENTIALS = {
    "nibelis": {
        "schema": REFERENTIAL_DIR / "nibelis-rubrics.schema.json",
        "catalog": REFERENTIAL_DIR / "nibelis-rubrics.example.json",
        "record_key": "rubrics",
        "id_field": "rubric_id",
        "code_field": "rubric_code",
    },
    "kelio": {
        "schema": REFERENTIAL_DIR / "kelio-counters.schema.json",
        "catalog": REFERENTIAL_DIR / "kelio-counters.example.json",
        "record_key": "counters",
        "id_field": "counter_id",
        "code_field": "counter_code",
    },
    "parameters": {
        "schema": REFERENTIAL_DIR / "payroll-parameters.schema.json",
        "catalog": REFERENTIAL_DIR / "payroll-parameters.example.json",
        "record_key": "parameters",
        "id_field": "parameter_id",
        "code_field": "parameter_code",
    },
}

DATE_FIELDS = {"effective_date", "end_date", "validated_at"}
CALCULATION_VALIDATION_STATUS = "human_validated"
CALCULATION_HUMAN_STATUS = "validated"
CALCULATION_CONFIDENCE = "high"
OPPOSABLE_OR_TRACEABLE_SOURCES = {
    "accord_entreprise",
    "convention_collective",
    "code_travail",
    "note_rh",
    "presentation_bulletin",
}

SENSITIVE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("email", re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.IGNORECASE)),
    ("iban", re.compile(r"\bFR\d{2}(?:\s?[A-Z0-9]){23}\b", re.IGNORECASE)),
    (
        "french_social_security_number",
        re.compile(r"\b[12][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{3}[\s.-]?\d{3}[\s.-]?\d{2}\b"),
    ),
    ("phone_number", re.compile(r"\b(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}\b")),
    ("matricule", re.compile(r"\b(?:matricule|employee\s*id|numero\s*salari[ee])\b", re.IGNORECASE)),
    (
        "personal_address",
        re.compile(r"\b\d{1,4}\s+(?:rue|avenue|boulevard|impasse|chemin|route|allee)\b", re.IGNORECASE),
    ),
)


@dataclass
class ReferentialIssue:
    code: str
    message: str
    field: str | None = None

    def as_dict(self) -> dict[str, str]:
        value = {"code": self.code, "message": self.message}
        if self.field:
            value["field"] = self.field
        return value


def load_json(path: Path | str) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_schema(kind: str) -> dict[str, Any]:
    if kind not in REFERENTIALS:
        raise ValueError(f"Unknown referential kind: {kind}")
    schema = load_json(REFERENTIALS[kind]["schema"])
    if not isinstance(schema, dict):
        raise ValueError(f"Invalid schema for {kind}: root must be an object")
    return schema


def load_catalog(kind: str) -> dict[str, Any]:
    if kind not in REFERENTIALS:
        raise ValueError(f"Unknown referential kind: {kind}")
    catalog = load_json(REFERENTIALS[kind]["catalog"])
    if not isinstance(catalog, dict):
        raise ValueError(f"Invalid catalog for {kind}: root must be an object")
    return catalog


def schema_issue(issue: rule_validator.ValidationIssue) -> ReferentialIssue:
    return ReferentialIssue(issue.code, issue.message, issue.field)


def parse_iso_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def iter_string_values(value: Any, path: str = "$") -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            values.extend(iter_string_values(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            values.extend(iter_string_values(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        values.append((path, value))
    return values


def collect_rule_reference_index() -> dict[str, set[str]]:
    catalog = rule_validator.load_catalog()
    rules = catalog.get("rules", [])
    rule_ids: set[str] = set()
    variables: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        rule_id = rule.get("rule_id")
        if isinstance(rule_id, str):
            rule_ids.add(rule_id)
        for variable in rule.get("required_variables") or []:
            if isinstance(variable, str):
                variables.add(variable)
    return {"rule_ids": rule_ids, "variables": variables}


def collect_referential_ids(catalogs: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    index = {
        "nibelis_rubric_ids": set(),
        "kelio_counter_ids": set(),
        "parameter_ids": set(),
    }
    for kind, catalog in catalogs.items():
        config = REFERENTIALS[kind]
        records = catalog.get(config["record_key"])
        if not isinstance(records, list):
            continue
        target_key = {
            "nibelis": "nibelis_rubric_ids",
            "kelio": "kelio_counter_ids",
            "parameters": "parameter_ids",
        }[kind]
        id_field = config["id_field"]
        for record in records:
            if isinstance(record, dict) and isinstance(record.get(id_field), str):
                index[target_key].add(record[id_field])
    return index


def default_reference_index(catalogs: dict[str, dict[str, Any]] | None = None) -> dict[str, set[str]]:
    index = collect_rule_reference_index()
    if catalogs is None:
        catalogs = {kind: load_catalog(kind) for kind in REFERENTIALS}
    index.update(collect_referential_ids(catalogs))
    return index


def check_unique_values(
    records: list[Any],
    *,
    field_name: str,
    path_prefix: str,
    issue_code: str,
) -> list[ReferentialIssue]:
    seen: dict[str, int] = {}
    issues: list[ReferentialIssue] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        value = record.get(field_name)
        if not isinstance(value, str):
            continue
        if value in seen:
            issues.append(
                ReferentialIssue(
                    issue_code,
                    f"Duplicate {field_name}: {value}",
                    f"{path_prefix}[{index}].{field_name}",
                )
            )
            issues.append(
                ReferentialIssue(
                    issue_code,
                    f"Duplicate {field_name}: {value}",
                    f"{path_prefix}[{seen[value]}].{field_name}",
                )
            )
            continue
        seen[value] = index
    return issues


def check_dates(record: dict[str, Any], path_prefix: str) -> list[ReferentialIssue]:
    issues: list[ReferentialIssue] = []
    for field_name in DATE_FIELDS:
        value = record.get(field_name)
        if value is not None and isinstance(value, str) and parse_iso_date(value) is None:
            issues.append(
                ReferentialIssue("invalid_date", f"Invalid ISO date for {field_name}: {value}", f"{path_prefix}.{field_name}")
            )
    effective_date = parse_iso_date(record.get("effective_date"))
    end_date = parse_iso_date(record.get("end_date"))
    if effective_date and end_date and effective_date > end_date:
        issues.append(
            ReferentialIssue(
                "effective_date_after_end_date",
                "effective_date must be earlier than or equal to end_date.",
                f"{path_prefix}.effective_date",
            )
        )
    human_validation = record.get("human_validation")
    if isinstance(human_validation, dict):
        validated_at = human_validation.get("validated_at")
        if validated_at is not None and isinstance(validated_at, str) and parse_iso_date(validated_at) is None:
            issues.append(
                ReferentialIssue(
                    "invalid_date",
                    f"Invalid ISO date for human_validation.validated_at: {validated_at}",
                    f"{path_prefix}.human_validation.validated_at",
                )
            )
    return issues


def check_sensitive_data(record: dict[str, Any], path_prefix: str) -> list[ReferentialIssue]:
    issues: list[ReferentialIssue] = []
    for path, value in iter_string_values(record, path_prefix):
        for code, pattern in SENSITIVE_PATTERNS:
            if pattern.search(value):
                issues.append(
                    ReferentialIssue(
                        "sensitive_data_detected",
                        f"Potential sensitive or personal data detected: {code}.",
                        path,
                    )
                )
    return issues


def check_links(record: dict[str, Any], reference_index: dict[str, set[str]], path_prefix: str) -> list[ReferentialIssue]:
    issues: list[ReferentialIssue] = []
    link_fields = {
        "linked_rule_ids": "rule_ids",
        "linked_variables": "variables",
        "linked_nibelis_rubric_ids": "nibelis_rubric_ids",
        "linked_kelio_counter_ids": "kelio_counter_ids",
    }
    for field_name, index_key in link_fields.items():
        if field_name not in record:
            continue
        values = record.get(field_name)
        if not isinstance(values, list):
            continue
        allowed_values = reference_index.get(index_key, set())
        seen: set[str] = set()
        for index, value in enumerate(values):
            if not isinstance(value, str):
                continue
            if value in seen:
                issues.append(
                    ReferentialIssue(
                        "duplicate_link",
                        f"Duplicate reference in {field_name}: {value}",
                        f"{path_prefix}.{field_name}[{index}]",
                    )
                )
            seen.add(value)
            if allowed_values and value not in allowed_values:
                issues.append(
                    ReferentialIssue(
                        "unknown_reference",
                        f"Unknown reference in {field_name}: {value}",
                        f"{path_prefix}.{field_name}[{index}]",
                    )
                )
    return issues


def check_synthetic_fixture_guard(record: dict[str, Any], path_prefix: str) -> list[ReferentialIssue]:
    issues: list[ReferentialIssue] = []
    if record.get("synthetic_only") is not True:
        issues.append(
            ReferentialIssue(
                "synthetic_fixture_not_marked",
                "Synthetic example records must keep synthetic_only = true.",
                f"{path_prefix}.synthetic_only",
            )
        )
    if record.get("calculation_allowed") is True:
        issues.append(
            ReferentialIssue(
                "synthetic_fixture_cannot_calculate",
                "Synthetic examples cannot be used for payroll calculation.",
                f"{path_prefix}.calculation_allowed",
            )
        )
    return issues


def check_calculation_gate(record: dict[str, Any], path_prefix: str) -> list[ReferentialIssue]:
    if record.get("calculation_allowed") is not True:
        return []

    issues: list[ReferentialIssue] = []
    if not record.get("source_document") or not record.get("source_reference"):
        issues.append(
            ReferentialIssue(
                "calculation_without_source",
                "calculation_allowed requires a source_document and a source_reference.",
                f"{path_prefix}.source_document",
            )
        )
    if record.get("source_layer") not in OPPOSABLE_OR_TRACEABLE_SOURCES:
        issues.append(
            ReferentialIssue(
                "calculation_with_untrusted_source_layer",
                "calculation_allowed requires a traceable non-synthetic source layer.",
                f"{path_prefix}.source_layer",
            )
        )
    if not parse_iso_date(record.get("effective_date")):
        issues.append(
            ReferentialIssue(
                "calculation_without_effective_date",
                "calculation_allowed requires a valid effective_date.",
                f"{path_prefix}.effective_date",
            )
        )
    if record.get("validation_status") != CALCULATION_VALIDATION_STATUS:
        issues.append(
            ReferentialIssue(
                "calculation_without_human_validation",
                "calculation_allowed requires validation_status = human_validated.",
                f"{path_prefix}.validation_status",
            )
        )
    if record.get("confidence") != CALCULATION_CONFIDENCE:
        issues.append(
            ReferentialIssue(
                "calculation_without_high_confidence",
                "calculation_allowed requires confidence = high.",
                f"{path_prefix}.confidence",
            )
        )
    if record.get("synthetic_only") is True:
        issues.append(
            ReferentialIssue(
                "calculation_from_synthetic_fixture",
                "calculation_allowed cannot be true for a synthetic fixture.",
                f"{path_prefix}.synthetic_only",
            )
        )
    human_validation = record.get("human_validation")
    if isinstance(human_validation, dict) and human_validation.get("status") != CALCULATION_HUMAN_STATUS:
        issues.append(
            ReferentialIssue(
                "calculation_without_validated_human_status",
                "calculation_allowed requires human_validation.status = validated.",
                f"{path_prefix}.human_validation.status",
            )
        )
    return issues


def validate_catalog(
    kind: str,
    catalog: dict[str, Any] | None = None,
    schema: dict[str, Any] | None = None,
    reference_index: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    if kind not in REFERENTIALS:
        raise ValueError(f"Unknown referential kind: {kind}")

    config = REFERENTIALS[kind]
    catalog = copy.deepcopy(catalog if catalog is not None else load_catalog(kind))
    schema = schema or load_schema(kind)
    reference_index = reference_index or default_reference_index()

    errors = [schema_issue(issue) for issue in rule_validator.validate_schema_node(catalog, schema, schema, "$")]
    records = catalog.get(config["record_key"]) if isinstance(catalog, dict) else []
    if not isinstance(records, list):
        records = []

    errors.extend(
        check_unique_values(
            records,
            field_name=str(config["id_field"]),
            path_prefix=str(config["record_key"]),
            issue_code="duplicate_identifier",
        )
    )
    errors.extend(
        check_unique_values(
            records,
            field_name=str(config["code_field"]),
            path_prefix=str(config["record_key"]),
            issue_code="duplicate_code",
        )
    )

    fixture_type = catalog.get("fixture_type") if isinstance(catalog, dict) else None
    for index, record in enumerate(records):
        path_prefix = f"{config['record_key']}[{index}]"
        if not isinstance(record, dict):
            continue
        errors.extend(check_dates(record, path_prefix))
        errors.extend(check_sensitive_data(record, path_prefix))
        errors.extend(check_links(record, reference_index, path_prefix))
        errors.extend(check_calculation_gate(record, path_prefix))
        if fixture_type == "synthetic_example":
            errors.extend(check_synthetic_fixture_guard(record, path_prefix))

    return {
        "kind": kind,
        "catalog": str(config["catalog"]),
        "schema": str(config["schema"]),
        "records_count": len(records),
        "valid": not errors,
        "errors_count": len(errors),
        "errors": [issue.as_dict() for issue in errors],
    }


def validate_all() -> dict[str, Any]:
    catalogs = {kind: load_catalog(kind) for kind in REFERENTIALS}
    reference_index = default_reference_index(catalogs)
    reports = {
        kind: validate_catalog(kind, catalog=catalogs[kind], schema=load_schema(kind), reference_index=reference_index)
        for kind in REFERENTIALS
    }
    return {
        "valid": all(report["valid"] for report in reports.values()),
        "errors_count": sum(int(report["errors_count"]) for report in reports.values()),
        "reports": reports,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate CFDT Nexus payroll referentials.")
    parser.add_argument("command", choices=["validate-all", "validate-catalog"])
    parser.add_argument("--kind", choices=sorted(REFERENTIALS), default="nibelis")
    args = parser.parse_args(argv)

    if args.command == "validate-all":
        report = validate_all()
    else:
        report = validate_catalog(args.kind)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
