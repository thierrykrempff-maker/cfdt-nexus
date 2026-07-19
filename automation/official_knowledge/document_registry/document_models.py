"""Generic immutable metadata models for the official Document Registry."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from hashlib import sha256
from typing import Any, Mapping


class DocumentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    UPDATED = "UPDATED"
    REMOVED = "REMOVED"
    REDIRECTED = "REDIRECTED"
    UNKNOWN = "UNKNOWN"


class ChangeKind(StrEnum):
    NEW = "NEW"
    UNCHANGED = "UNCHANGED"
    TITLE_CHANGED = "TITLE_CHANGED"
    DATE_CHANGED = "DATE_CHANGED"
    CATEGORY_CHANGED = "CATEGORY_CHANGED"
    FAMILY_CHANGED = "FAMILY_CHANGED"
    DOCUMENT_TYPE_CHANGED = "DOCUMENT_TYPE_CHANGED"
    METADATA_CHANGED = "METADATA_CHANGED"
    REMOVED = "REMOVED"
    REDIRECTED = "REDIRECTED"


@dataclass(frozen=True)
class DocumentRecord:
    """Metadata-only representation shared by every official connector."""

    document_id: str
    connector_name: str
    canonical_url: str
    title: str
    category: str
    family: str
    document_type: str
    publication_date: str | None
    first_seen: str
    last_checked: str
    last_modified_metadata: str
    language: str
    provenance: str
    status: DocumentStatus = DocumentStatus.ACTIVE

    def __post_init__(self) -> None:
        if not isinstance(self.status, DocumentStatus):
            raise TypeError("status must be a DocumentStatus")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DocumentRecord":
        allowed = {item.name for item in cls.__dataclass_fields__.values()}
        unknown = set(value) - allowed
        if unknown:
            raise ValueError(f"unknown document fields: {sorted(unknown)}")
        return cls(
            document_id=value.get("document_id"), connector_name=value.get("connector_name"),
            canonical_url=value.get("canonical_url"), title=value.get("title"),
            category=value.get("category"), family=value.get("family"),
            document_type=value.get("document_type"), publication_date=value.get("publication_date"),
            first_seen=value.get("first_seen"), last_checked=value.get("last_checked"),
            last_modified_metadata=value.get("last_modified_metadata"), language=value.get("language"),
            provenance=value.get("provenance"), status=DocumentStatus(value.get("status")),
        )


@dataclass(frozen=True)
class DocumentChange:
    document_id: str
    kind: ChangeKind
    previous: DocumentRecord | None
    current: DocumentRecord
    changed_fields: tuple[str, ...] = ()


def stable_document_id(connector_name: str, canonical_url: str) -> str:
    """Return a stable connector-scoped identifier without retaining content."""
    material = f"{connector_name.strip()}\n{canonical_url.strip()}".encode("utf-8")
    return sha256(material).hexdigest()
