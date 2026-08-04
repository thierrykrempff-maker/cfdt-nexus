"""Local, explicit and privacy-bounded storage for union case files.

The store is deliberately outside Git (``local-index`` by default). Reading never
creates a directory; persistence happens only after an explicit user action.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import secrets
from typing import Any


SCHEMA_VERSION = 1
ALLOWED_STATUSES = {"OPEN", "IN_PROGRESS", "WAITING", "CLOSED", "CANCELLED"}
MAX_TEXT = 6000
MAX_LIST_ITEMS = 40
CASE_REF_RE = re.compile(r"^DOSSIER-\d{8}-\d{6}-[A-F0-9]{4}$")
FORBIDDEN_KEY_RE = re.compile(
    r"(?:^|_)(?:origin_session_id|case_session_id|plan_id|event_id|query_id|"
    r"target_id|issue_id|fact_id|document_id|chunk_id|storage_id|"
    r"authorization|token|secret|password)(?:$|_)",
    re.IGNORECASE,
)
FORBIDDEN_TEXT_RE = re.compile(
    r"(?:[A-Za-z]:\\|/home/|/Users/|/tmp/|Bearer\s+[A-Za-z0-9._~-]+)",
    re.IGNORECASE,
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: Any, limit: int = MAX_TEXT) -> str:
    rendered = " ".join(str(value or "").split())[:limit].strip()
    if FORBIDDEN_TEXT_RE.search(rendered):
        raise ValueError("Le dossier contient une information technique non autorisée.")
    return rendered


def _public_value(value: Any, *, depth: int = 0) -> Any:
    if depth > 5:
        return None
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            key = str(raw_key)
            if FORBIDDEN_KEY_RE.search(key):
                continue
            projected = _public_value(raw_value, depth=depth + 1)
            if projected not in (None, "", [], {}):
                clean[key] = projected
        return clean
    if isinstance(value, (list, tuple)):
        return [
            item
            for item in (
                _public_value(item, depth=depth + 1)
                for item in value[:MAX_LIST_ITEMS]
            )
            if item not in (None, "", [], {})
        ]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return value
    return _text(value)


def _case_ref() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"DOSSIER-{stamp}-{secrets.token_hex(2).upper()}"


def _decision(raw: Any) -> dict[str, str]:
    value = raw if isinstance(raw, dict) else {}
    return {
        "date": _text(value.get("date"), 40),
        "type": _text(value.get("type"), 120),
        "author_role": _text(value.get("author_role"), 180),
        "summary": _text(value.get("summary")),
        "supporting_document": _text(value.get("supporting_document"), 500),
    }


class LocalCaseStore:
    def __init__(self, root: Path):
        self.root = Path(root)

    def _path(self, case_ref: str) -> Path:
        if not CASE_REF_RE.fullmatch(case_ref):
            raise ValueError("Référence de dossier invalide.")
        return self.root / f"{case_ref}.json"

    def list_cases(self) -> list[dict[str, Any]]:
        if not self.root.is_dir():
            return []
        rows = []
        for path in sorted(self.root.glob("DOSSIER-*.json"), reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            rows.append(
                {
                    "case_ref": data.get("case_ref", ""),
                    "title": data.get("title", ""),
                    "status": data.get("status", "OPEN"),
                    "updated_at": data.get("updated_at", ""),
                    "decision_recorded": bool(
                        data.get("final_decision", {}).get("summary")
                    ),
                }
            )
        return rows

    def get_case(self, case_ref: str) -> dict[str, Any]:
        path = self._path(case_ref)
        if not path.is_file():
            raise KeyError("Dossier local introuvable.")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Dossier local illisible.") from exc
        return _public_value(data)

    def save_case(self, raw: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(raw, dict):
            raise ValueError("Dossier local invalide.")
        existing_ref = _text(raw.get("case_ref"), 80)
        case_ref = existing_ref or _case_ref()
        path = self._path(case_ref)
        previous: dict[str, Any] = {}
        if path.is_file():
            try:
                previous = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError("Le dossier existant est illisible.") from exc

        title = _text(raw.get("title"), 240)
        if not title:
            raise ValueError("Le titre du dossier est obligatoire.")
        status = _text(raw.get("status"), 40).upper() or "OPEN"
        if status not in ALLOWED_STATUSES:
            raise ValueError("Statut de dossier invalide.")

        created_at = str(previous.get("created_at") or _now())
        data = {
            "schema_version": SCHEMA_VERSION,
            "case_ref": case_ref,
            "title": title,
            "status": status,
            "created_at": created_at,
            "updated_at": _now(),
            "question": _text(raw.get("question")),
            "public_summary": _public_value(raw.get("public_summary") or {}),
            "follow_up_answers": _public_value(raw.get("follow_up_answers") or []),
            "documents": _public_value(raw.get("documents") or []),
            "uploaded_documents": _public_value(raw.get("uploaded_documents") or []),
            "actions": _public_value(raw.get("actions") or []),
            "notes": _text(raw.get("notes")),
            "final_decision": _decision(raw.get("final_decision")),
            "privacy_notice": (
                "Dossier syndical local pseudonymisé. Ne pas y conserver de donnée "
                "personnelle ou médicale inutile."
            ),
        }
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return _public_value(data)

    def delete_case(self, case_ref: str) -> None:
        path = self._path(case_ref)
        if not path.is_file():
            raise KeyError("Dossier local introuvable.")
        path.unlink()
