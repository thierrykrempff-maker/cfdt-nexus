"""Replaceable persistence boundary and deterministic local JSON storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .document_models import DocumentRecord


class DocumentStorage(Protocol):
    def load(self) -> tuple[DocumentRecord, ...]: ...
    def save(self, documents: tuple[DocumentRecord, ...]) -> None: ...


class JsonDocumentStorage:
    """Local JSON persistence with no retained in-memory document cache."""

    SCHEMA_VERSION = "1.0"

    def __init__(self, path: Path) -> None:
        resolved = Path(path)
        if resolved.suffix.lower() != ".json":
            raise ValueError("registry storage path must use .json")
        self.path = resolved

    def load(self) -> tuple[DocumentRecord, ...]:
        if not self.path.exists():
            return ()
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("document registry JSON is unreadable") from exc
        if not isinstance(value, dict) or set(value) != {"schema_version", "documents"}:
            raise ValueError("invalid document registry structure")
        if value["schema_version"] != self.SCHEMA_VERSION or not isinstance(value["documents"], list):
            raise ValueError("unsupported document registry schema")
        documents = tuple(DocumentRecord.from_dict(item) for item in value["documents"])
        identifiers = tuple(item.document_id for item in documents)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("duplicate document_id in storage")
        return tuple(sorted(documents, key=lambda item: item.document_id))

    def save(self, documents: tuple[DocumentRecord, ...]) -> None:
        if not isinstance(documents, tuple) or any(not isinstance(item, DocumentRecord) for item in documents):
            raise TypeError("documents must be a tuple of DocumentRecord")
        ordered = tuple(sorted(documents, key=lambda item: item.document_id))
        identifiers = tuple(item.document_id for item in ordered)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("duplicate document_id")
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "documents": [item.to_dict() for item in ordered],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.path)
