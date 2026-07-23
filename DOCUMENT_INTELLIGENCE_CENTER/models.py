"""Immutable, metadata-only models for documentary intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Iterable


class DocumentKind(str, Enum):
    """Document families understood by the documentary graph."""

    AGREEMENT = "AGREEMENT"
    CSE_MINUTES = "CSE_MINUTES"
    CSSCT_MINUTES = "CSSCT_MINUTES"
    AGENDA = "AGENDA"
    LEGAL_TEXT = "LEGAL_TEXT"
    CASE_LAW = "CASE_LAW"
    GUIDE = "GUIDE"
    STUDY = "STUDY"
    OTHER = "OTHER"


class RelationKind(str, Enum):
    """Directed relationships supported by the documentary graph."""

    REFERENCES = "REFERENCES"
    SUPERSEDES = "SUPERSEDES"
    AMENDS = "AMENDS"
    IMPLEMENTS = "IMPLEMENTS"
    DISCUSSES = "DISCUSSES"
    DECIDES_ON = "DECIDES_ON"
    APPLIES_TO = "APPLIES_TO"
    RELATED_TO = "RELATED_TO"


def _clean_tuple(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({value.strip() for value in values if value.strip()}))


@dataclass(frozen=True, slots=True)
class DocumentDescriptor:
    """A content-free description of a document known to Nexus.

    The model deliberately has no field for text, chunks, local paths, binary
    payloads or embeddings. Existing repositories keep ownership of those
    concerns; this layer only indexes stable references and public metadata.
    """

    document_id: str
    title: str
    document_kind: DocumentKind
    provenance: str
    canonical_url: str | None = None
    publication_date: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    version_label: str | None = None
    family: str | None = None
    language: str = "fr"
    topics: tuple[str, ...] = field(default_factory=tuple)
    referenced_document_ids: tuple[str, ...] = field(default_factory=tuple)
    referenced_canonical_urls: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for field_name in ("document_id", "title", "provenance", "language"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required")
        if not isinstance(self.document_kind, DocumentKind):
            raise TypeError("document_kind must be a DocumentKind")
        object.__setattr__(self, "document_id", self.document_id.strip())
        object.__setattr__(self, "title", self.title.strip())
        object.__setattr__(self, "provenance", self.provenance.strip())
        object.__setattr__(self, "language", self.language.strip().lower())
        object.__setattr__(self, "topics", _clean_tuple(self.topics))
        object.__setattr__(
            self,
            "referenced_document_ids",
            _clean_tuple(self.referenced_document_ids),
        )
        object.__setattr__(
            self,
            "referenced_canonical_urls",
            _clean_tuple(self.referenced_canonical_urls),
        )


@dataclass(frozen=True, slots=True)
class DocumentRelation:
    """A deterministic directed edge between two document descriptors."""

    source_document_id: str
    target_document_id: str
    relation_kind: RelationKind
    provenance: str
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.source_document_id or not self.target_document_id:
            raise ValueError("relation endpoints are required")
        if self.source_document_id == self.target_document_id:
            raise ValueError("a document cannot relate to itself")
        if not isinstance(self.relation_kind, RelationKind):
            raise TypeError("relation_kind must be a RelationKind")
        if not self.provenance.strip():
            raise ValueError("relation provenance is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

    @property
    def relation_id(self) -> str:
        material = "\n".join(
            (
                self.source_document_id,
                self.relation_kind.value,
                self.target_document_id,
            )
        ).encode("utf-8")
        return sha256(material).hexdigest()
