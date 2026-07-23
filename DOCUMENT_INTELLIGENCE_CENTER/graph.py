"""Deterministic in-memory documentary graph.

The graph stores descriptors and relations only. Persistence, document
retrieval and content indexing remain outside this LOT.
"""

from __future__ import annotations

from collections import deque
from typing import Iterable

from .models import DocumentDescriptor, DocumentRelation, RelationKind


class DocumentGraphError(ValueError):
    """Raised when a graph invariant would be violated."""


class DocumentGraph:
    """Index relationships between immutable document descriptors."""

    def __init__(
        self,
        documents: Iterable[DocumentDescriptor] = (),
        relations: Iterable[DocumentRelation] = (),
    ) -> None:
        self._documents: dict[str, DocumentDescriptor] = {}
        self._relations: dict[str, DocumentRelation] = {}
        for document in documents:
            self.add_document(document)
        for relation in relations:
            self.add_relation(relation)

    def add_document(self, document: DocumentDescriptor) -> None:
        current = self._documents.get(document.document_id)
        if current is not None and current != document:
            raise DocumentGraphError(
                f"document_id already registered: {document.document_id}"
            )
        self._documents[document.document_id] = document

    def add_relation(self, relation: DocumentRelation) -> None:
        missing = {
            item
            for item in (relation.source_document_id, relation.target_document_id)
            if item not in self._documents
        }
        if missing:
            raise DocumentGraphError(
                f"relation references unknown documents: {sorted(missing)}"
            )
        current = self._relations.get(relation.relation_id)
        if current is not None and current != relation:
            raise DocumentGraphError(
                f"relation_id already registered: {relation.relation_id}"
            )
        self._relations[relation.relation_id] = relation

    def find_document(self, document_id: str) -> DocumentDescriptor | None:
        return self._documents.get(document_id)

    def documents(self) -> tuple[DocumentDescriptor, ...]:
        return tuple(self._documents[key] for key in sorted(self._documents))

    def relations(self) -> tuple[DocumentRelation, ...]:
        return tuple(self._relations[key] for key in sorted(self._relations))

    def outgoing(
        self,
        document_id: str,
        relation_kind: RelationKind | None = None,
    ) -> tuple[DocumentRelation, ...]:
        return tuple(
            relation
            for relation in self.relations()
            if relation.source_document_id == document_id
            and (relation_kind is None or relation.relation_kind is relation_kind)
        )

    def incoming(
        self,
        document_id: str,
        relation_kind: RelationKind | None = None,
    ) -> tuple[DocumentRelation, ...]:
        return tuple(
            relation
            for relation in self.relations()
            if relation.target_document_id == document_id
            and (relation_kind is None or relation.relation_kind is relation_kind)
        )

    def related_document_ids(
        self,
        document_id: str,
        relation_kinds: Iterable[RelationKind] | None = None,
        max_depth: int = 1,
    ) -> tuple[str, ...]:
        """Return a deterministic, undirected neighbourhood projection."""

        if max_depth < 1:
            raise ValueError("max_depth must be at least 1")
        allowed = set(relation_kinds) if relation_kinds is not None else None
        visited = {document_id}
        queue = deque([(document_id, 0)])
        while queue:
            current, depth = queue.popleft()
            if depth == max_depth:
                continue
            for relation in self.relations():
                if allowed is not None and relation.relation_kind not in allowed:
                    continue
                neighbour = None
                if relation.source_document_id == current:
                    neighbour = relation.target_document_id
                elif relation.target_document_id == current:
                    neighbour = relation.source_document_id
                if neighbour is not None and neighbour not in visited:
                    visited.add(neighbour)
                    queue.append((neighbour, depth + 1))
        visited.discard(document_id)
        return tuple(sorted(visited))
