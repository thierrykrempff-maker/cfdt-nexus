#!/usr/bin/env python
"""Extensible, data-only export engine for synthetic case reports (LOT 5E)."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
from typing import Any, Callable, Mapping


EXPORT_ENGINE_VERSION = "1.0"


class ExportFormat(str, Enum):
    json = "json"
    markdown = "markdown"
    text = "text"


class ExportPrivacy(str, Enum):
    standard = "standard"
    employee = "employee"
    expert = "expert"


FORMAT_EXTENSIONS = {
    ExportFormat.json: "json",
    ExportFormat.markdown: "md",
    ExportFormat.text: "txt",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _safe_identifier(value: Any) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_-]+", "-", str(value or "CASE-UNKNOWN")).strip("-")
    return normalized or "CASE-UNKNOWN"


def _title(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _markdown(value: Any, *, level: int = 1) -> str:
    lines: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            heading = "#" * min(level, 6)
            lines.append(f"{heading} {_title(str(key))}")
            lines.append("")
            lines.append(_markdown(item, level=level + 1).rstrip())
            lines.append("")
    elif isinstance(value, list):
        if not value:
            lines.append("_Aucun élément._")
        for item in value:
            if isinstance(item, (Mapping, list)):
                rendered = _markdown(item, level=level + 1).strip().replace("\n", "\n  ")
                lines.append(f"- {rendered}")
            else:
                lines.append(f"- {item}")
    elif value is None:
        lines.append("Non renseigné")
    elif isinstance(value, bool):
        lines.append("Oui" if value else "Non")
    else:
        lines.append(str(value))
    return "\n".join(lines).rstrip() + "\n"


def _plain_text(value: Any, *, prefix: str = "") -> str:
    lines: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            label = f"{prefix}{_title(str(key))}"
            if isinstance(item, (Mapping, list)):
                lines.append(label)
                lines.append(_plain_text(item, prefix=prefix + "  ").rstrip())
            else:
                lines.append(f"{label}: {'Non renseigné' if item is None else item}")
    elif isinstance(value, list):
        if not value:
            lines.append(f"{prefix}Aucun élément")
        for item in value:
            if isinstance(item, (Mapping, list)):
                lines.append(f"{prefix}-")
                lines.append(_plain_text(item, prefix=prefix + "  ").rstrip())
            else:
                lines.append(f"{prefix}- {item}")
    else:
        lines.append(f"{prefix}{value}")
    return "\n".join(lines).rstrip() + "\n"


class ReportExporter:
    """Project and render an existing report without invoking, calculating or writing."""

    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._renderers = {
            ExportFormat.json: lambda payload: deepcopy(payload),
            ExportFormat.markdown: _markdown,
            ExportFormat.text: _plain_text,
        }

    def export(
        self,
        source: Mapping[str, Any],
        export_format: ExportFormat | str,
        privacy: ExportPrivacy | str = ExportPrivacy.standard,
    ) -> dict[str, Any]:
        original = deepcopy(source)
        data = deepcopy(dict(source))
        if not data.get("synthetic_only"):
            raise ValueError("Only synthetic_only reports can be exported.")
        kind = self._source_kind(data)
        selected_format = ExportFormat(export_format)
        selected_privacy = ExportPrivacy(privacy)
        payload = self._project(data, selected_privacy)
        content = self._renderers[selected_format](payload)
        logical_content = _canonical_json(content) if selected_format is ExportFormat.json else str(content)
        fingerprint = hashlib.sha256(logical_content.encode("utf-8")).hexdigest()
        generated_at = self._utc_now()
        case_id = self._case_identifier(data, payload, kind, selected_privacy)
        source_version = self._source_version(data, kind)
        filename = self._filename(case_id, generated_at, kind, source_version, selected_format)
        logical_path = f"{generated_at.year:04d}/{_safe_identifier(case_id)}/{filename}"
        result = {
            "export_type": "employee_case_report_export",
            "source_type": kind,
            "content": content,
            "metadata": {
                "export_engine_version": EXPORT_ENGINE_VERSION,
                "source_version": source_version,
                "generated_at_utc": generated_at.isoformat().replace("+00:00", "Z"),
                "format": selected_format.value,
                "privacy": selected_privacy.value,
                "logical_fingerprint_algorithm": "sha256",
                "logical_fingerprint": fingerprint,
                "filename": filename,
                "logical_archive_path": logical_path,
                "archive_year": generated_at.year,
                "case_identifier": _safe_identifier(case_id),
                "automatic_disk_write": False,
                "synthetic_only": True,
            },
            "disk_write_performed": False,
            "calculation_performed": False,
            "expert_invocation_performed": False,
        }
        if source != original:
            raise RuntimeError("The source report was unexpectedly mutated.")
        return result

    @staticmethod
    def _source_kind(data: Mapping[str, Any]) -> str:
        if data.get("report_type") == "employee_case_analysis":
            return "report"
        if data.get("comparison_type") == "employee_case_documentary_comparison":
            return "comparison"
        raise ValueError("Unsupported source: expected a LOT 5B report or LOT 5D comparison.")

    @staticmethod
    def _project(data: Mapping[str, Any], privacy: ExportPrivacy) -> dict[str, Any]:
        if privacy is ExportPrivacy.standard:
            return deepcopy(dict(data))
        view_key = "employee_view" if privacy is ExportPrivacy.employee else "expert_view"
        view = data.get(view_key)
        if not isinstance(view, Mapping):
            raise ValueError(f"The selected source has no {view_key} mapping.")
        return deepcopy(dict(view))

    def _utc_now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).replace(microsecond=0)

    @staticmethod
    def _case_identifier(
        data: Mapping[str, Any], payload: Mapping[str, Any], kind: str, privacy: ExportPrivacy
    ) -> str:
        if privacy is not ExportPrivacy.standard:
            if kind == "report":
                header = payload.get("header") if isinstance(payload.get("header"), Mapping) else {}
                sections = payload.get("sections") if isinstance(payload.get("sections"), Mapping) else {}
                section_header = sections.get("header") if isinstance(sections.get("header"), Mapping) else {}
                return str(header.get("case_id") or section_header.get("case_id") or "REPORT")
            return "COMPARISON"
        if kind == "report":
            sections = data.get("sections") if isinstance(data.get("sections"), Mapping) else {}
            header = sections.get("header") if isinstance(sections.get("header"), Mapping) else {}
            return str(header.get("case_id") or "CASE-UNKNOWN")
        inputs = data.get("inputs") if isinstance(data.get("inputs"), Mapping) else {}
        left = inputs.get("case_a") if isinstance(inputs.get("case_a"), Mapping) else {}
        right = inputs.get("case_b") if isinstance(inputs.get("case_b"), Mapping) else {}
        return f"{left.get('case_id') or 'CASE-A'}--{right.get('case_id') or 'CASE-B'}"

    @staticmethod
    def _source_version(data: Mapping[str, Any], kind: str) -> str:
        if kind == "comparison":
            return str(data.get("comparator_version") or "unknown")
        sections = data.get("sections") if isinstance(data.get("sections"), Mapping) else {}
        metadata = sections.get("metadata") if isinstance(sections.get("metadata"), Mapping) else {}
        return str(metadata.get("report_version") or "unknown")

    @staticmethod
    def _filename(
        case_id: str,
        generated_at: datetime,
        kind: str,
        version: str,
        export_format: ExportFormat,
    ) -> str:
        safe_version = _safe_identifier(version)
        return (
            f"{_safe_identifier(case_id)}_{generated_at.date().isoformat()}_"
            f"{kind}_v{safe_version}.{FORMAT_EXTENSIONS[export_format]}"
        )
