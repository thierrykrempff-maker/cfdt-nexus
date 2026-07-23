"""Agreement version-chain management based on explicit metadata relations."""

from __future__ import annotations

from dataclasses import dataclass

from .graph import DocumentGraph, DocumentGraphError
from .models import DocumentDescriptor, DocumentKind, RelationKind


@dataclass(frozen=True, slots=True)
class AgreementVersionReport:
    """Deterministic view of an agreement family and its current version."""

    family: str
    ordered_document_ids: tuple[str, ...]
    current_document_ids: tuple[str, ...]
    has_ambiguity: bool


class AgreementVersionManager:
    """Resolve agreement histories without interpreting document contents."""

    VERSION_RELATIONS = (RelationKind.SUPERSEDES, RelationKind.AMENDS)

    def __init__(self, graph: DocumentGraph) -> None:
        self._graph = graph

    def describe_family(self, family: str) -> AgreementVersionReport:
        documents = tuple(
            document
            for document in self._graph.documents()
            if document.document_kind is DocumentKind.AGREEMENT
            and document.family == family
        )
        if not documents:
            return AgreementVersionReport(family, (), (), False)
        family_ids = {document.document_id for document in documents}
        relations = tuple(
            relation
            for relation in self._graph.relations()
            if relation.relation_kind in self.VERSION_RELATIONS
            and relation.source_document_id in family_ids
            and relation.target_document_id in family_ids
        )
        self._ensure_acyclic(family_ids, relations)
        superseded = {relation.target_document_id for relation in relations}
        current_ids = tuple(sorted(family_ids - superseded))
        ordered = tuple(
            document.document_id
            for document in sorted(
                documents,
                key=lambda item: (
                    item.effective_from or "",
                    item.publication_date or "",
                    item.version_label or "",
                    item.document_id,
                ),
            )
        )
        return AgreementVersionReport(
            family=family,
            ordered_document_ids=ordered,
            current_document_ids=current_ids,
            has_ambiguity=len(current_ids) != 1,
        )

    @staticmethod
    def _ensure_acyclic(document_ids, relations) -> None:
        successors = {document_id: set() for document_id in document_ids}
        for relation in relations:
            successors[relation.source_document_id].add(
                relation.target_document_id
            )
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(document_id: str) -> None:
            if document_id in visiting:
                raise DocumentGraphError("agreement version cycle detected")
            if document_id in visited:
                return
            visiting.add(document_id)
            for target_id in successors[document_id]:
                visit(target_id)
            visiting.remove(document_id)
            visited.add(document_id)

        for document_id in sorted(document_ids):
            visit(document_id)
