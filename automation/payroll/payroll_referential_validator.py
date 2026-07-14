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
    "knowledge_graph": {
        "schema": REFERENTIAL_DIR / "payroll-knowledge-graph.schema.json",
        "catalog": REFERENTIAL_DIR / "payroll-knowledge-graph.example.json",
        "record_key": "relations",
        "id_field": "relation_id",
        "code_field": "relation_id",
    },
}

DATE_FIELDS = {"effective_date", "end_date", "validated_at", "last_checked_at"}
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
KELIO_REQUIRED_TEXT_FIELDS = ("business_description",)
KELIO_REQUIRED_LIST_FIELDS = (
    "feed_conditions",
    "decrease_conditions",
    "documents_to_check",
    "frequent_anomalies",
    "control_points",
    "synthetic_reading_examples",
)
NIBELIS_REQUIRED_TEXT_FIELDS = ("business_description", "generic_source")
NIBELIS_REQUIRED_LIST_FIELDS = (
    "documents_to_check",
    "frequent_anomalies",
    "control_points",
    "synthetic_reading_examples",
)
PARAMETER_REQUIRED_TEXT_FIELDS = ("business_description", "source_document")
PARAMETER_REQUIRED_LIST_FIELDS = ("validation_documents", "misuse_risks")
PARAMETER_ALLOWED_VALIDATORS = {
    None,
    "expert_paie_humain",
    "referent_cfdt_humain",
    "validateur_metier_humain",
}
PARAMETER_VALUE_UNKNOWN_STATES = {"identified_value_unknown", "awaiting_source"}
PARAMETER_READY_STATE = "calculation_ready"
PARAMETER_TYPE_UNITS = {
    "rate": {"rate_percent"},
    "amount": {"amount_eur"},
    "threshold": {"hours", "days", "count", "km", "amount_eur"},
    "date": {"date"},
    "duration": {"hours", "days"},
    "distance": {"km"},
    "method": {"text", "none"},
    "formula_component": {"amount_eur", "hours", "days", "rate_percent", "count", "km", "text"},
    "ceiling": {"amount_eur", "hours", "days", "count", "km"},
    "period": {"date", "text"},
    "informational": {"text", "none"},
    "other": {"amount_eur", "hours", "days", "rate_percent", "count", "date", "km", "text", "none"},
}
PARAMETER_NUMERIC_TYPES = {"amount", "threshold", "duration", "distance", "formula_component", "ceiling"}
PARAMETER_METHOD_TYPES = {"method", "informational", "period", "date"}
KNOWLEDGE_GRAPH_RELATION_TYPES = {
    "uses_parameter",
    "uses_variable",
    "feeds_counter",
    "feeds_rubric",
    "explains_rubric",
    "derived_from",
    "requires_document",
    "requires_validation",
    "may_trigger",
    "controls",
    "depends_on",
}
KNOWLEDGE_GRAPH_COMPATIBLE_TYPES = {
    "uses_parameter": {("rule", "payroll_parameter")},
    "uses_variable": {("rule", "variable")},
    "feeds_counter": {("variable", "kelio_counter")},
    "feeds_rubric": {("kelio_counter", "nibelis_rubric")},
    "explains_rubric": {("payroll_parameter", "nibelis_rubric")},
    "derived_from": {("payroll_parameter", "variable"), ("nibelis_rubric", "kelio_counter")},
    "requires_document": {("rule", "payroll_parameter"), ("payroll_parameter", "rule")},
    "requires_validation": {("rule", "payroll_parameter"), ("payroll_parameter", "rule")},
    "may_trigger": {("rule", "nibelis_rubric")},
    "controls": {("rule", "kelio_counter"), ("payroll_parameter", "kelio_counter")},
    "depends_on": {("rule", "kelio_counter"), ("payroll_parameter", "variable")},
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
        "knowledge_relation_ids": set(),
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
            "knowledge_graph": "knowledge_relation_ids",
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
    application_period = record.get("application_period")
    if isinstance(application_period, dict):
        start_date_value = application_period.get("start_date")
        end_date_value = application_period.get("end_date")
        if start_date_value is not None and isinstance(start_date_value, str) and parse_iso_date(start_date_value) is None:
            issues.append(
                ReferentialIssue(
                    "invalid_date",
                    f"Invalid ISO date for application_period.start_date: {start_date_value}",
                    f"{path_prefix}.application_period.start_date",
                )
            )
        if end_date_value is not None and isinstance(end_date_value, str) and parse_iso_date(end_date_value) is None:
            issues.append(
                ReferentialIssue(
                    "invalid_date",
                    f"Invalid ISO date for application_period.end_date: {end_date_value}",
                    f"{path_prefix}.application_period.end_date",
                )
            )
        start_date = parse_iso_date(start_date_value)
        period_end_date = parse_iso_date(end_date_value)
        if start_date and period_end_date and start_date > period_end_date:
            issues.append(
                ReferentialIssue(
                    "application_period_start_after_end",
                    "application_period.start_date must be earlier than or equal to application_period.end_date.",
                    f"{path_prefix}.application_period.start_date",
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


def check_required_business_documentation(
    record: dict[str, Any],
    path_prefix: str,
    *,
    label: str,
    text_fields: tuple[str, ...],
    list_fields: tuple[str, ...],
) -> list[ReferentialIssue]:
    issues: list[ReferentialIssue] = []
    for field_name in text_fields:
        value = record.get(field_name)
        if not isinstance(value, str) or not value.strip():
            issues.append(
                ReferentialIssue(
                    "missing_business_documentation",
                    f"{label} must document {field_name}.",
                    f"{path_prefix}.{field_name}",
                )
            )
    for field_name in list_fields:
        value = record.get(field_name)
        if not isinstance(value, list) or not value:
            issues.append(
                ReferentialIssue(
                    "missing_business_documentation",
                    f"{label} must provide at least one item in {field_name}.",
                    f"{path_prefix}.{field_name}",
                )
            )
            continue
        if not any(item for item in value):
            issues.append(
                ReferentialIssue(
                    "missing_business_documentation",
                    f"{label} documentation field is empty: {field_name}.",
                    f"{path_prefix}.{field_name}",
                )
            )
    return issues


def check_nibelis_documentation(record: dict[str, Any], path_prefix: str) -> list[ReferentialIssue]:
    return check_required_business_documentation(
        record,
        path_prefix,
        label="Nibelis rubric",
        text_fields=NIBELIS_REQUIRED_TEXT_FIELDS,
        list_fields=NIBELIS_REQUIRED_LIST_FIELDS,
    )


def check_nibelis_business_rules(record: dict[str, Any], path_prefix: str) -> list[ReferentialIssue]:
    issues: list[ReferentialIssue] = []
    normalized_label = str(record.get("normalized_label") or "").lower()
    sub_category = str(record.get("sub_category") or "").lower()
    gross_impact = record.get("gross_impact")
    affects_gross = record.get("affects_gross")

    if ("retenue" in normalized_label or "retenue" in sub_category) and gross_impact != "negative":
        issues.append(
            ReferentialIssue(
                "nibelis_retenue_must_be_negative",
                "A deduction/retention rubric must declare gross_impact = negative.",
                f"{path_prefix}.gross_impact",
            )
        )

    if gross_impact == "informational" and affects_gross is not False:
        issues.append(
            ReferentialIssue(
                "nibelis_informational_cannot_affect_gross",
                "An informational rubric cannot affect gross pay.",
                f"{path_prefix}.affects_gross",
            )
        )

    if record.get("category") == "counter_information" and gross_impact != "informational":
        issues.append(
            ReferentialIssue(
                "nibelis_counter_information_must_be_informational",
                "A counter information rubric must use gross_impact = informational.",
                f"{path_prefix}.gross_impact",
            )
        )

    if record.get("appears_on_payslip") is False:
        description_text = " ".join(
            str(value or "")
            for value in [
                record.get("label"),
                record.get("business_description"),
                " ".join(record.get("notes") or []) if isinstance(record.get("notes"), list) else "",
            ]
        ).lower()
        visible_markers = ("visible sur le bulletin", "presente sur le bulletin", "apparait sur le bulletin")
        if any(marker in description_text for marker in visible_markers):
            issues.append(
                ReferentialIssue(
                    "nibelis_hidden_rubric_described_as_visible",
                    "A rubric with appears_on_payslip = false cannot be described as visible on the payslip.",
                    f"{path_prefix}.appears_on_payslip",
                )
            )

    if record.get("appears_on_payslip") is True and record.get("anonymization_required") is not True:
        issues.append(
            ReferentialIssue(
                "nibelis_anonymization_required",
                "A payslip rubric must explicitly require anonymization before any real data is used.",
                f"{path_prefix}.anonymization_required",
            )
        )

    return issues


def check_parameter_documentation(record: dict[str, Any], path_prefix: str) -> list[ReferentialIssue]:
    return check_required_business_documentation(
        record,
        path_prefix,
        label="Payroll parameter",
        text_fields=PARAMETER_REQUIRED_TEXT_FIELDS,
        list_fields=PARAMETER_REQUIRED_LIST_FIELDS,
    )


def check_parameter_value_rules(record: dict[str, Any], path_prefix: str) -> list[ReferentialIssue]:
    issues: list[ReferentialIssue] = []
    parameter_id = record.get("parameter_id")
    parameter_code = record.get("parameter_code")
    if isinstance(parameter_id, str) and not parameter_id.endswith("_SYN"):
        issues.append(
            ReferentialIssue(
                "synthetic_parameter_id_must_end_with_syn",
                "Synthetic parameter identifiers must end with _SYN.",
                f"{path_prefix}.parameter_id",
            )
        )
    if isinstance(parameter_code, str) and not parameter_code.endswith("_SYN"):
        issues.append(
            ReferentialIssue(
                "synthetic_parameter_code_must_end_with_syn",
                "Synthetic parameter codes must end with _SYN.",
                f"{path_prefix}.parameter_code",
            )
        )

    verified_by = record.get("verified_by")
    if verified_by not in PARAMETER_ALLOWED_VALIDATORS:
        issues.append(
            ReferentialIssue(
                "parameter_validator_must_be_generic_role",
                "verified_by must use a generic role, not a real person.",
                f"{path_prefix}.verified_by",
            )
        )
    human_validation = record.get("human_validation")
    if isinstance(human_validation, dict) and human_validation.get("validator") not in PARAMETER_ALLOWED_VALIDATORS:
        issues.append(
            ReferentialIssue(
                "parameter_validator_must_be_generic_role",
                "human_validation.validator must use a generic role, not a real person.",
                f"{path_prefix}.human_validation.validator",
            )
        )

    parameter_type = record.get("parameter_type")
    value_state = record.get("value_state")
    value = record.get("value")

    if not isinstance(value, dict):
        return issues

    unit = value.get("unit")
    numeric_value = value.get("numeric_value")
    percentage = value.get("percentage")
    currency = value.get("currency")
    raw = str(value.get("raw") or "").lower()

    allowed_units = PARAMETER_TYPE_UNITS.get(str(parameter_type), set())
    if allowed_units and unit not in allowed_units:
        issues.append(
            ReferentialIssue(
                "parameter_unit_incompatible_with_type",
                f"Unit {unit} is incompatible with parameter_type {parameter_type}.",
                f"{path_prefix}.value.unit",
            )
        )

    if currency is not None and unit != "amount_eur":
        issues.append(
            ReferentialIssue(
                "parameter_currency_incompatible_with_unit",
                "currency is only allowed when unit = amount_eur.",
                f"{path_prefix}.value.currency",
            )
        )
    if unit == "amount_eur" and numeric_value is not None and currency != "EUR":
        issues.append(
            ReferentialIssue(
                "parameter_currency_required_for_amount",
                "A numeric amount_eur parameter must declare currency = EUR.",
                f"{path_prefix}.value.currency",
            )
        )

    if percentage is not None and unit != "rate_percent":
        issues.append(
            ReferentialIssue(
                "parameter_percentage_incompatible_with_unit",
                "percentage is only allowed when unit = rate_percent.",
                f"{path_prefix}.value.percentage",
            )
        )
    if unit == "rate_percent" and percentage is None and numeric_value is not None:
        issues.append(
            ReferentialIssue(
                "parameter_rate_without_percentage",
                "A rate_percent parameter with a numeric value must declare percentage.",
                f"{path_prefix}.value.percentage",
            )
        )
    if isinstance(percentage, (int, float)) and not 0 <= float(percentage) <= 300:
        issues.append(
            ReferentialIssue(
                "parameter_percentage_out_of_range",
                "Percentage parameters must stay in a conservative 0..300 range.",
                f"{path_prefix}.value.percentage",
            )
        )

    if parameter_type == "rate" and unit == "rate_percent" and numeric_value is not None and percentage is not None:
        if abs(float(numeric_value) - float(percentage)) > 0.00001:
            issues.append(
                ReferentialIssue(
                    "parameter_rate_value_mismatch",
                    "For rate parameters, numeric_value and percentage must match.",
                    f"{path_prefix}.value.numeric_value",
                )
            )

    if parameter_type in PARAMETER_NUMERIC_TYPES and unit not in {"text", "none", "date"} and value_state not in PARAMETER_VALUE_UNKNOWN_STATES:
        if numeric_value is None:
            issues.append(
                ReferentialIssue(
                    "parameter_numeric_value_missing",
                    "Numeric parameter types require numeric_value unless the value is explicitly unknown.",
                    f"{path_prefix}.value.numeric_value",
                )
            )
    if parameter_type in PARAMETER_METHOD_TYPES and unit in {"text", "none", "date"} and parameter_type != "date" and numeric_value is not None:
        issues.append(
            ReferentialIssue(
                "parameter_method_has_numeric_value",
                "Method or informational parameters must not carry a numeric value.",
                f"{path_prefix}.value.numeric_value",
            )
        )
    if parameter_type == "date" and numeric_value is not None:
        issues.append(
            ReferentialIssue(
                "parameter_date_has_numeric_value",
                "Date parameters must store the date in raw, not numeric_value.",
                f"{path_prefix}.value.numeric_value",
            )
        )

    if value_state in PARAMETER_VALUE_UNKNOWN_STATES and (numeric_value is not None or percentage is not None):
        issues.append(
            ReferentialIssue(
                "parameter_unknown_value_cannot_be_numeric",
                "Unknown or awaiting-source parameters cannot carry an exploitable numeric value.",
                f"{path_prefix}.value.numeric_value",
            )
        )
    if value_state in PARAMETER_VALUE_UNKNOWN_STATES and record.get("calculation_allowed") is True:
        issues.append(
            ReferentialIssue(
                "parameter_unknown_value_cannot_calculate",
                "A parameter without a known value cannot be calculation_allowed.",
                f"{path_prefix}.calculation_allowed",
            )
        )

    if value.get("is_fallback_value") is True or "valeur par defaut" in raw or "default" in raw:
        issues.append(
            ReferentialIssue(
                "parameter_fallback_value_forbidden",
                "Fallback/default values are forbidden unless replaced by a sourced validated value.",
                f"{path_prefix}.value.is_fallback_value",
            )
        )

    claims_validated = (
        record.get("validation_status") == CALCULATION_VALIDATION_STATUS
        or record.get("confidence") == CALCULATION_CONFIDENCE
        or value_state == PARAMETER_READY_STATE
    )
    if claims_validated:
        if not isinstance(human_validation, dict) or human_validation.get("status") != CALCULATION_HUMAN_STATUS:
            issues.append(
                ReferentialIssue(
                    "parameter_claims_validation_without_human_validation",
                    "A validated/high-confidence/calculation-ready parameter requires human_validation.status = validated.",
                    f"{path_prefix}.human_validation.status",
                )
            )

    return issues


def periods_overlap(left_start: date | None, left_end: date | None, right_start: date | None, right_end: date | None) -> bool:
    if left_start is None or right_start is None:
        return False
    left_limit = left_end or date.max
    right_limit = right_end or date.max
    return left_start <= right_limit and right_start <= left_limit


def check_parameter_exclusive_periods(records: list[Any], path_prefix: str) -> list[ReferentialIssue]:
    issues: list[ReferentialIssue] = []
    by_group: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        group = record.get("mutually_exclusive_group")
        if isinstance(group, str) and group.strip():
            by_group.setdefault(group, []).append((index, record))

    for group, grouped_records in by_group.items():
        for left_position, (left_index, left_record) in enumerate(grouped_records):
            left_start = parse_iso_date(left_record.get("effective_date"))
            left_end = parse_iso_date(left_record.get("end_date"))
            for right_index, right_record in grouped_records[left_position + 1 :]:
                right_start = parse_iso_date(right_record.get("effective_date"))
                right_end = parse_iso_date(right_record.get("end_date"))
                if periods_overlap(left_start, left_end, right_start, right_end):
                    issues.append(
                        ReferentialIssue(
                            "exclusive_parameters_overlap",
                            f"Mutually exclusive parameters overlap in group {group}: {left_record.get('parameter_id')} / {right_record.get('parameter_id')}.",
                            f"{path_prefix}[{right_index}].mutually_exclusive_group",
                        )
                    )
    return issues


def knowledge_graph_object_ids(reference_index: dict[str, set[str]]) -> dict[str, set[str]]:
    return {
        "rule": reference_index.get("rule_ids", set()),
        "variable": reference_index.get("variables", set()),
        "kelio_counter": reference_index.get("kelio_counter_ids", set()),
        "nibelis_rubric": reference_index.get("nibelis_rubric_ids", set()),
        "payroll_parameter": reference_index.get("parameter_ids", set()),
    }


def check_knowledge_graph(
    catalog: dict[str, Any],
    records: list[Any],
    reference_index: dict[str, set[str]],
    path_prefix: str,
) -> list[ReferentialIssue]:
    issues: list[ReferentialIssue] = []
    object_ids = knowledge_graph_object_ids(reference_index)
    relation_ids = {
        record.get("relation_id")
        for record in records
        if isinstance(record, dict) and isinstance(record.get("relation_id"), str)
    }
    covered_rules: set[str] = set()
    seen_edges: set[tuple[tuple[str, str], tuple[str, str]]] = set()

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        relation_path = f"{path_prefix}[{index}]"
        relation_id = record.get("relation_id")
        source_type = record.get("source_type")
        target_type = record.get("target_type")
        source_id = record.get("source_id")
        target_id = record.get("target_id")
        relation_type = record.get("relation_type")

        if record.get("synthetic_only") is not True:
            issues.append(
                ReferentialIssue(
                    "knowledge_graph_relation_not_synthetic",
                    "Knowledge graph relations in example fixtures must keep synthetic_only = true.",
                    f"{relation_path}.synthetic_only",
                )
            )
        if record.get("calculation_allowed") is not False:
            issues.append(
                ReferentialIssue(
                    "knowledge_graph_relation_cannot_calculate",
                    "Knowledge graph relations cannot authorize payroll calculation.",
                    f"{relation_path}.calculation_allowed",
                )
            )

        if isinstance(source_type, str) and isinstance(source_id, str):
            if source_id not in object_ids.get(source_type, set()):
                issues.append(
                    ReferentialIssue(
                        "knowledge_graph_unknown_reference",
                        f"Unknown source reference: {source_type}:{source_id}",
                        f"{relation_path}.source_id",
                    )
                )
            if source_type == "rule":
                covered_rules.add(source_id)
        if isinstance(target_type, str) and isinstance(target_id, str):
            if target_id not in object_ids.get(target_type, set()):
                issues.append(
                    ReferentialIssue(
                        "knowledge_graph_unknown_reference",
                        f"Unknown target reference: {target_type}:{target_id}",
                        f"{relation_path}.target_id",
                    )
                )

        if isinstance(relation_type, str) and relation_type in KNOWLEDGE_GRAPH_RELATION_TYPES:
            allowed_pairs = KNOWLEDGE_GRAPH_COMPATIBLE_TYPES.get(relation_type, set())
            if (source_type, target_type) not in allowed_pairs:
                issues.append(
                    ReferentialIssue(
                        "knowledge_graph_incompatible_relation",
                        f"Relation {relation_type} is not compatible with {source_type} -> {target_type}.",
                        f"{relation_path}.relation_type",
                    )
                )

        if (
            isinstance(source_type, str)
            and isinstance(target_type, str)
            and isinstance(source_id, str)
            and isinstance(target_id, str)
        ):
            source_node = (source_type, source_id)
            target_node = (target_type, target_id)
            if source_node == target_node:
                issues.append(
                    ReferentialIssue(
                        "knowledge_graph_direct_loop",
                        f"Direct self-loop is forbidden for relation {relation_id}.",
                        f"{relation_path}.target_id",
                    )
                )
            if (target_node, source_node) in seen_edges:
                issues.append(
                    ReferentialIssue(
                        "knowledge_graph_direct_cycle",
                        f"Direct reverse cycle is forbidden for relation {relation_id}.",
                        f"{relation_path}.target_id",
                    )
                )
            seen_edges.add((source_node, target_node))

    missing_rules = sorted(reference_index.get("rule_ids", set()) - covered_rules)
    for rule_id in missing_rules:
        issues.append(
            ReferentialIssue(
                "knowledge_graph_missing_rule_coverage",
                f"Payroll rule is not covered by the knowledge graph: {rule_id}",
                path_prefix,
            )
        )

    scenarios = catalog.get("scenarios")
    if isinstance(scenarios, list):
        for index, scenario in enumerate(scenarios):
            if not isinstance(scenario, dict):
                continue
            scenario_path = f"scenarios[{index}]"
            if scenario.get("synthetic_only") is not True:
                issues.append(
                    ReferentialIssue(
                        "knowledge_graph_scenario_not_synthetic",
                        "Knowledge graph scenarios in example fixtures must keep synthetic_only = true.",
                        f"{scenario_path}.synthetic_only",
                    )
                )
            if scenario.get("calculation_allowed") is not False:
                issues.append(
                    ReferentialIssue(
                        "knowledge_graph_scenario_cannot_calculate",
                        "Knowledge graph scenarios cannot authorize payroll calculation.",
                        f"{scenario_path}.calculation_allowed",
                    )
                )
            starting_type = scenario.get("starting_object_type")
            starting_id = scenario.get("starting_object_id")
            if isinstance(starting_type, str) and isinstance(starting_id, str):
                if starting_id not in object_ids.get(starting_type, set()):
                    issues.append(
                        ReferentialIssue(
                            "knowledge_graph_unknown_reference",
                            f"Unknown scenario starting object: {starting_type}:{starting_id}",
                            f"{scenario_path}.starting_object_id",
                        )
                    )
            relation_refs = scenario.get("relation_ids")
            if isinstance(relation_refs, list):
                for ref_index, relation_ref in enumerate(relation_refs):
                    if isinstance(relation_ref, str) and relation_ref not in relation_ids:
                        issues.append(
                            ReferentialIssue(
                                "knowledge_graph_unknown_relation",
                                f"Unknown relation referenced by scenario: {relation_ref}",
                                f"{scenario_path}.relation_ids[{ref_index}]",
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
    if "value_state" in record and record.get("value_state") != PARAMETER_READY_STATE:
        issues.append(
            ReferentialIssue(
                "calculation_without_ready_parameter_state",
                "calculation_allowed requires value_state = calculation_ready.",
                f"{path_prefix}.value_state",
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
    if config["code_field"] != config["id_field"]:
        errors.extend(
            check_unique_values(
                records,
                field_name=str(config["code_field"]),
                path_prefix=str(config["record_key"]),
                issue_code="duplicate_code",
            )
        )
    if kind == "parameters":
        errors.extend(check_parameter_exclusive_periods(records, str(config["record_key"])))
    if kind == "knowledge_graph":
        errors.extend(check_knowledge_graph(catalog, records, reference_index, str(config["record_key"])))

    fixture_type = catalog.get("fixture_type") if isinstance(catalog, dict) else None
    for index, record in enumerate(records):
        path_prefix = f"{config['record_key']}[{index}]"
        if not isinstance(record, dict):
            continue
        errors.extend(check_dates(record, path_prefix))
        errors.extend(check_sensitive_data(record, path_prefix))
        errors.extend(check_links(record, reference_index, path_prefix))
        errors.extend(check_calculation_gate(record, path_prefix))
        if kind == "kelio":
            errors.extend(
                check_required_business_documentation(
                    record,
                    path_prefix,
                    label="Kelio counter",
                    text_fields=KELIO_REQUIRED_TEXT_FIELDS,
                    list_fields=KELIO_REQUIRED_LIST_FIELDS,
                )
            )
        if kind == "nibelis":
            errors.extend(check_nibelis_documentation(record, path_prefix))
            errors.extend(check_nibelis_business_rules(record, path_prefix))
        if kind == "parameters":
            errors.extend(check_parameter_documentation(record, path_prefix))
            errors.extend(check_parameter_value_rules(record, path_prefix))
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
