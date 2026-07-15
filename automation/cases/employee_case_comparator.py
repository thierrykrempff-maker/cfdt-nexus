#!/usr/bin/env python
"""Document-only comparator for synthetic employee cases and reports (LOT 5D)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

from .employee_case import EmployeeCase


COMPARATOR_VERSION = "1.0"
DIFFERENCE_CATEGORIES = ("new", "removed", "modified", "unchanged")
CONFIDENCE_ORDER = {"UNKNOWN": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "VERY_HIGH": 4}


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _json_value(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_value(item) for item in value]
    return value


def _unique(values: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    for value in values:
        if value not in result and value not in (None, "", [], {}):
            result.append(value)
    return result


def _as_list(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    if isinstance(value, (list, tuple, set, frozenset)):
        return list(value)
    return [value]


def _collection_delta(before: Iterable[Any], after: Iterable[Any]) -> dict[str, list[Any]]:
    left = _unique(before)
    right = _unique(after)
    return {
        "new": [item for item in right if item not in left],
        "removed": [item for item in left if item not in right],
        "modified": [],
        "unchanged": [item for item in left if item in right],
    }


def _scalar_delta(before: Any, after: Any) -> dict[str, Any]:
    if before == after:
        category = "unchanged"
    elif before in (None, "", [], {}):
        category = "new"
    elif after in (None, "", [], {}):
        category = "removed"
    else:
        category = "modified"
    return {"category": category, "before": before, "after": after}


def _report_sections(value: Mapping[str, Any]) -> Mapping[str, Any]:
    sections = value.get("sections")
    return sections if isinstance(sections, Mapping) else {}


def _normalize_report(value: Mapping[str, Any]) -> dict[str, Any]:
    sections = _report_sections(value)
    header = sections.get("header") if isinstance(sections.get("header"), Mapping) else {}
    situation = sections.get("analyzed_situation") if isinstance(sections.get("analyzed_situation"), Mapping) else {}
    documents = sections.get("documents") if isinstance(sections.get("documents"), Mapping) else {}
    confidence = sections.get("confidence") if isinstance(sections.get("confidence"), Mapping) else {}
    contradictions = sections.get("contradictions") if isinstance(sections.get("contradictions"), Mapping) else {}
    actions = sections.get("recommended_actions") if isinstance(sections.get("recommended_actions"), Mapping) else {}
    metadata = sections.get("metadata") if isinstance(sections.get("metadata"), Mapping) else {}
    themes = {}
    for item in _as_list(sections.get("theme_analysis")):
        if isinstance(item, Mapping) and item.get("theme"):
            themes[str(item["theme"])] = deepcopy(dict(item))
    experts = {}
    for key in ("payroll_expert_summary", "legal_expert_summary"):
        item = sections.get(key)
        if isinstance(item, Mapping):
            experts[key] = deepcopy(dict(item))
    return {
        "source_type": "report",
        "case_id": header.get("case_id") or metadata.get("source_case_id"),
        "title": header.get("title"),
        "period": situation.get("period"),
        "status": header.get("status"),
        "themes": themes,
        "documents_present": _as_list(documents.get("present")),
        "documents_missing": _as_list(documents.get("missing")),
        "documents_blocking": _as_list(documents.get("blocking")),
        "completeness": {
            key: item.get("status") for key, item in themes.items() if isinstance(item, Mapping)
        },
        "confidence": confidence.get("global_level", "UNKNOWN"),
        "contradictions": _as_list(contradictions.get("items")),
        "experts": experts,
        "actions": {str(key): _as_list(item) for key, item in actions.items() if key != "warning"},
        "synthetic_only": bool(value.get("synthetic_only") and metadata.get("synthetic_only", True)),
    }


def _normalize_case(value: EmployeeCase | Mapping[str, Any]) -> dict[str, Any]:
    data = value.as_dict() if isinstance(value, EmployeeCase) else _json_value(value)
    if not isinstance(data, Mapping):
        raise TypeError("Each comparison input must be an EmployeeCase or a mapping.")
    if data.get("report_type") == "employee_case_analysis" or "sections" in data:
        return _normalize_report(data)
    documents = _as_list(data.get("documents"))
    present = []
    missing = list(_as_list(data.get("missing_documents")))
    for document in documents:
        if not isinstance(document, Mapping):
            continue
        identifier = document.get("document_id") or document.get("document_type")
        if document.get("availability", "present") == "present":
            present.append(identifier)
        else:
            missing.append(document.get("document_type") or identifier)
    themes = {
        str(theme): {
            "theme": str(theme),
            "status": "documented",
            "missing_documents": [],
            "documents_used": present,
            "findings": [],
            "limits": ["Raw case: no expert report supplied."],
        }
        for theme in _as_list(data.get("detected_themes"))
    }
    return {
        "source_type": "case",
        "case_id": data.get("case_id"),
        "title": data.get("title"),
        "period": data.get("period"),
        "status": data.get("status"),
        "themes": themes,
        "documents_present": _unique(present),
        "documents_missing": _unique(missing),
        "documents_blocking": [],
        "completeness": {key: "not_assessed" for key in themes},
        "confidence": "UNKNOWN",
        "contradictions": [],
        "experts": {},
        "actions": {},
        "synthetic_only": bool(data.get("synthetic_only")),
    }


class EmployeeCaseComparator:
    """Compare already available data without calculation or legal inference."""

    def compare(
        self,
        case_a: EmployeeCase | Mapping[str, Any],
        case_b: EmployeeCase | Mapping[str, Any],
    ) -> dict[str, Any]:
        original_a = deepcopy(case_a)
        original_b = deepcopy(case_b)
        left = _normalize_case(deepcopy(case_a))
        right = _normalize_case(deepcopy(case_b))
        if not left["synthetic_only"] or not right["synthetic_only"]:
            raise ValueError("The comparator accepts synthetic_only inputs exclusively.")

        dimensions = {
            "period": _scalar_delta(left["period"], right["period"]),
            "status": _scalar_delta(left["status"], right["status"]),
            "themes": _collection_delta(left["themes"], right["themes"]),
            "documents_present": _collection_delta(left["documents_present"], right["documents_present"]),
            "documents_missing": _collection_delta(left["documents_missing"], right["documents_missing"]),
            "completeness": self._mapping_delta(left["completeness"], right["completeness"]),
            "confidence": _scalar_delta(left["confidence"], right["confidence"]),
            "contradictions": _collection_delta(left["contradictions"], right["contradictions"]),
            "expert_analyses": self._mapping_delta(left["experts"], right["experts"]),
            "recommended_actions": self._mapping_delta(left["actions"], right["actions"]),
        }
        theme_analysis = self._theme_analysis(left, right)
        detected = self._detect_contradictions(left, right, theme_analysis)
        substantive = [name for name, delta in dimensions.items() if not self._unchanged(delta)]
        presentation = {
            "title": _scalar_delta(left["title"], right["title"]),
            "case_id": _scalar_delta(left["case_id"], right["case_id"]),
        }
        newly_required = _unique(
            (*dimensions["documents_missing"]["new"], *right["documents_blocking"])
        )
        blocked_a = {key for key, item in left["themes"].items() if item.get("status") == "blocked"}
        blocked_b = {key for key, item in right["themes"].items() if item.get("status") == "blocked"}
        summary = {
            "changed_dimensions": substantive,
            "unchanged_dimensions": [name for name in dimensions if name not in substantive],
            "new_documents_needed": newly_required,
            "newly_blocked_themes": sorted(blocked_b - blocked_a),
            "newly_unblocked_themes": sorted(blocked_a - blocked_b),
            "caution": "No certain cause is assigned without supporting documentary evidence.",
        }
        result = {
            "comparison_type": "employee_case_documentary_comparison",
            "comparator_version": COMPARATOR_VERSION,
            "inputs": {
                "case_a": {"case_id": left["case_id"], "source_type": left["source_type"]},
                "case_b": {"case_id": right["case_id"], "source_type": right["source_type"]},
            },
            "difference_categories": list(DIFFERENCE_CATEGORIES),
            "executive_summary": summary,
            "substantive_differences": dimensions,
            "presentation_differences": presentation,
            "theme_analysis": theme_analysis,
            "detected_contradictions": detected,
            "employee_view": self._employee_view(summary, theme_analysis, detected),
            "expert_view": self._expert_view(dimensions, presentation, theme_analysis, detected),
            "limits": [
                "The comparison is documentary and does not recalculate payroll.",
                "A difference is not interpreted as a payroll error.",
                "No definitive legal conclusion is produced.",
                "Only information already present in the two inputs is compared.",
            ],
            "calculation_performed": False,
            "expert_invocation_performed": False,
            "synthetic_only": True,
        }
        if case_a != original_a or case_b != original_b:
            raise RuntimeError("Comparison inputs were unexpectedly mutated.")
        return result

    @staticmethod
    def _mapping_delta(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
        result = {category: [] for category in DIFFERENCE_CATEGORIES}
        for key in sorted(set(before) | set(after)):
            delta = _scalar_delta(before.get(key), after.get(key))
            result[delta["category"]].append({"key": key, "before": delta["before"], "after": delta["after"]})
        return result

    @staticmethod
    def _unchanged(delta: Mapping[str, Any]) -> bool:
        if "category" in delta:
            return delta["category"] == "unchanged"
        return not any(delta.get(category) for category in ("new", "removed", "modified"))

    def _theme_analysis(self, left: Mapping[str, Any], right: Mapping[str, Any]) -> list[dict[str, Any]]:
        result = []
        for theme in sorted(set(left["themes"]) | set(right["themes"])):
            before = left["themes"].get(theme)
            after = right["themes"].get(theme)
            delta = _scalar_delta(before, after)
            missing_before = _as_list(before.get("missing_documents")) if isinstance(before, Mapping) else []
            missing_after = _as_list(after.get("missing_documents")) if isinstance(after, Mapping) else []
            result.append(
                {
                    "theme": theme,
                    "state_a": deepcopy(before),
                    "state_b": deepcopy(after),
                    "difference_category": delta["category"],
                    "documentary_consequences": _collection_delta(missing_before, missing_after),
                    "new_documents_to_request": [item for item in missing_after if item not in missing_before],
                }
            )
        return result

    @staticmethod
    def _detect_contradictions(
        left: Mapping[str, Any], right: Mapping[str, Any], themes: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        if CONFIDENCE_ORDER.get(str(right["confidence"]), 0) < CONFIDENCE_ORDER.get(str(left["confidence"]), 0):
            findings.append({"type": "confidence_decrease", "message": "Confidence is lower in case B."})
        document_delta = _collection_delta(left["documents_present"], right["documents_present"])
        if document_delta["new"] or document_delta["removed"]:
            findings.append({"type": "document_presence_changed", "message": "Document availability differs between cases."})
        new_documents = set(document_delta["new"])
        for item in themes:
            before = item["state_a"] or {}
            after = item["state_b"] or {}
            if before.get("status") == "blocked" and after.get("status") != "blocked" and not new_documents:
                findings.append(
                    {"type": "unblocked_without_new_document", "message": f"Theme {item['theme']} is unblocked without a new document."}
                )
        for expert in sorted(set(left["experts"]) & set(right["experts"])):
            before = left["experts"][expert]
            after = right["experts"][expert]
            if before.get("available") and after.get("available") and before.get("findings") and after.get("findings"):
                if set(before["findings"]).isdisjoint(after["findings"]):
                    findings.append(
                        {"type": "incompatible_expert_findings", "message": f"Expert findings differ materially for {expert}."}
                    )
        return findings

    @staticmethod
    def _employee_view(
        summary: Mapping[str, Any], themes: list[dict[str, Any]], contradictions: list[dict[str, str]]
    ) -> dict[str, Any]:
        return {
            "audience": "employee",
            "what_changed": list(summary["changed_dimensions"]),
            "what_did_not_change": list(summary["unchanged_dimensions"]),
            "documents_to_request": list(summary["new_documents_needed"]),
            "blocked_themes": list(summary["newly_blocked_themes"]),
            "unblocked_themes": list(summary["newly_unblocked_themes"]),
            "themes": [
                {"theme": item["theme"], "change": item["difference_category"], "documents_to_request": item["new_documents_to_request"]}
                for item in themes
            ],
            "warnings": [item["message"] for item in contradictions],
            "explanation": "These changes describe the supplied documents; they do not establish a payroll error.",
        }

    @staticmethod
    def _expert_view(
        dimensions: Mapping[str, Any],
        presentation: Mapping[str, Any],
        themes: list[dict[str, Any]],
        contradictions: list[dict[str, str]],
    ) -> dict[str, Any]:
        return {
            "audience": "expert",
            "substantive_differences": deepcopy(dict(dimensions)),
            "presentation_differences": deepcopy(dict(presentation)),
            "theme_analysis": deepcopy(themes),
            "documentary_controls": deepcopy(contradictions),
            "limits": "Differences require documentary verification and do not prove a payroll or legal error.",
        }
