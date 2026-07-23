"""Public contracts preparing future documentary and semantic search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .graph import DocumentGraph


@dataclass(frozen=True, slots=True)
class SearchDocument:
    """Metadata-only projection suitable for a future search backend."""

    document_id: str
    title: str
    document_type: str
    provenance: str
    publication_date: str | None
    topics: tuple[str, ...]
    related_document_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SearchQuery:
    """Backend-neutral query contract; no embedding implementation is imposed."""

    query_text: str
    document_types: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    limit: int = 10

    def __post_init__(self) -> None:
        if not self.query_text.strip():
            raise ValueError("query_text is required")
        if not 1 <= self.limit <= 100:
            raise ValueError("limit must be between 1 and 100")


@dataclass(frozen=True, slots=True)
class SearchHit:
    """A stable search result referencing a document without copying content."""

    document_id: str
    score: float
    matched_metadata_fields: tuple[str, ...] = ()


@runtime_checkable
class DocumentSearchBackend(Protocol):
    """Replaceable future search implementation."""

    def index(self, documents: tuple[SearchDocument, ...]) -> None:
        """Index metadata projections."""

    def search(self, query: SearchQuery) -> tuple[SearchHit, ...]:
        """Return stable document references ordered by relevance."""


class SearchProjectionBuilder:
    """Build deterministic metadata projections from the documentary graph."""

    def build(self, graph: DocumentGraph) -> tuple[SearchDocument, ...]:
        return tuple(
            SearchDocument(
                document_id=document.document_id,
                title=document.title,
                document_type=document.document_kind.value,
                provenance=document.provenance,
                publication_date=document.publication_date,
                topics=document.topics,
                related_document_ids=graph.related_document_ids(
                    document.document_id
                ),
            )
            for document in graph.documents()
        )
