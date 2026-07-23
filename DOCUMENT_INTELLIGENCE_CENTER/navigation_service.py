"""Read-only, deterministic API for documentary graph navigation."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from .graph import DocumentGraph
from .ingestion_models import is_pseudonymous_id
from .metadata_index import MetadataIndex, MetadataQuery
from .models import (
    DocumentDescriptor,
    DocumentKind,
    DocumentRelation,
    RelationKind,
)
from .navigation_models import (
    GraphPath,
    GraphStatistics,
    NavigationDirection,
    NavigationDocument,
    NavigationQuery,
    NavigationResult,
)
from .versioning import AgreementVersionManager


class DocumentNavigationService:
    """Expose stable graph traversal without expert or Runtime dependencies."""

    _MINUTES_KINDS = (DocumentKind.CSE_MINUTES, DocumentKind.CSSCT_MINUTES)
    _MINUTES_RELATIONS = (
        RelationKind.REFERENCES,
        RelationKind.DISCUSSES,
        RelationKind.DECIDES_ON,
    )

    def __init__(self, graph: DocumentGraph) -> None:
        self._graph = graph

    def get_document(self, document_id: str) -> NavigationDocument | None:
        self._validate_identifier(document_id)
        document = self._graph.find_document(document_id)
        return self._view(document) if document is not None else None

    def search(self, query: NavigationQuery) -> NavigationResult:
        index = MetadataIndex(self._graph.documents())
        documents = index.find(
            MetadataQuery(
                document_id=query.document_id,
                document_kind=query.document_kind,
                date_from=query.date_from,
                date_to=query.date_to,
                instance=query.instance,
                family=query.family,
                status=query.status,
            )
        )
        if query.document_id is None:
            return NavigationResult(
                query,
                tuple(self._view(item) for item in documents),
            )
        related_ids, relations = self._walk(query)
        selected = {
            item.document_id: item
            for item in documents
        }
        for document_id in related_ids:
            document = self._graph.find_document(document_id)
            if document is not None:
                selected[document_id] = document
        return NavigationResult(
            query,
            tuple(self._view(selected[key]) for key in sorted(selected)),
            relations,
        )

    def outgoing(
        self,
        document_id: str,
        relation_kinds: Iterable[RelationKind] = (),
    ) -> NavigationResult:
        return self.search(
            NavigationQuery(
                document_id=document_id,
                relation_kinds=tuple(relation_kinds),
                direction=NavigationDirection.OUTGOING,
            )
        )

    def related_documents(
        self,
        document_id: str,
        *,
        max_depth: int = 1,
        relation_kinds: Iterable[RelationKind] = (),
    ) -> NavigationResult:
        return self.search(
            NavigationQuery(
                document_id=document_id,
                relation_kinds=tuple(relation_kinds),
                direction=NavigationDirection.BOTH,
                max_depth=max_depth,
            )
        )

    def incoming(
        self,
        document_id: str,
        relation_kinds: Iterable[RelationKind] = (),
    ) -> NavigationResult:
        return self.search(
            NavigationQuery(
                document_id=document_id,
                relation_kinds=tuple(relation_kinds),
                direction=NavigationDirection.INCOMING,
            )
        )

    def agreement_versions(
        self,
        *,
        family: str | None = None,
        document_id: str | None = None,
    ) -> NavigationResult:
        if family is None:
            if document_id is None:
                raise ValueError("family or document_id is required")
            document = self._graph.find_document(document_id)
            if document is None or document.document_kind is not DocumentKind.AGREEMENT:
                return NavigationResult(NavigationQuery(document_id=document_id), ())
            family = document.family
        if not family:
            return NavigationResult(NavigationQuery(family=family), ())
        report = AgreementVersionManager(self._graph).describe_family(family)
        documents = tuple(
            self._view(self._graph.find_document(item))
            for item in report.ordered_document_ids
        )
        version_ids = set(report.ordered_document_ids)
        relations = tuple(
            relation
            for relation in self._graph.relations()
            if relation.relation_kind
            in (RelationKind.SUPERSEDES, RelationKind.AMENDS)
            and relation.source_document_id in version_ids
            and relation.target_document_id in version_ids
        )
        return NavigationResult(
            NavigationQuery(family=family),
            documents,
            relations,
        )

    def replaced_or_modified(self, document_id: str) -> NavigationResult:
        return self.search(
            NavigationQuery(
                document_id=document_id,
                relation_kinds=(
                    RelationKind.SUPERSEDES,
                    RelationKind.AMENDS,
                ),
                direction=NavigationDirection.BOTH,
            )
        )

    def minutes_for_agreement(self, document_id: str) -> NavigationResult:
        result = self.incoming(document_id, self._MINUTES_RELATIONS)
        documents = tuple(
            item
            for item in result.documents
            if item.document_id == document_id
            or item.document_kind in self._MINUTES_KINDS
        )
        return NavigationResult(result.query, documents, result.relations)

    def agreements_for_minutes(self, document_id: str) -> NavigationResult:
        result = self.outgoing(document_id, self._MINUTES_RELATIONS)
        documents = tuple(
            item
            for item in result.documents
            if item.document_id == document_id
            or item.document_kind is DocumentKind.AGREEMENT
        )
        return NavigationResult(result.query, documents, result.relations)

    def shortest_path(
        self,
        source_document_id: str,
        target_document_id: str,
    ) -> GraphPath:
        self._validate_identifier(source_document_id)
        self._validate_identifier(target_document_id)
        if self._graph.find_document(source_document_id) is None:
            return GraphPath((), ())
        if self._graph.find_document(target_document_id) is None:
            return GraphPath((), ())
        if source_document_id == target_document_id:
            return GraphPath((source_document_id,), ())
        adjacency = self._adjacency()
        queue = deque([(source_document_id, (source_document_id,), ())])
        visited = {source_document_id}
        while queue:
            current, document_path, relation_path = queue.popleft()
            for neighbour, relation_id in adjacency[current]:
                if neighbour in visited:
                    continue
                next_documents = document_path + (neighbour,)
                next_relations = relation_path + (relation_id,)
                if neighbour == target_document_id:
                    return GraphPath(next_documents, next_relations)
                visited.add(neighbour)
                queue.append((neighbour, next_documents, next_relations))
        return GraphPath((), ())

    def orphan_document_ids(self) -> tuple[str, ...]:
        related = {
            endpoint
            for relation in self._graph.relations()
            for endpoint in (
                relation.source_document_id,
                relation.target_document_id,
            )
        }
        orphan_ids = tuple(
            item.document_id
            for item in self._graph.documents()
            if item.document_id not in related
        )
        self._validate_identifiers(orphan_ids)
        return orphan_ids

    def connected_components(self) -> tuple[tuple[str, ...], ...]:
        adjacency = self._adjacency()
        self._validate_identifiers(adjacency)
        remaining = set(adjacency)
        components: list[tuple[str, ...]] = []
        while remaining:
            start = min(remaining)
            queue = deque([start])
            component = {start}
            remaining.remove(start)
            while queue:
                current = queue.popleft()
                for neighbour, _relation_id in adjacency[current]:
                    if neighbour in remaining:
                        remaining.remove(neighbour)
                        component.add(neighbour)
                        queue.append(neighbour)
            components.append(tuple(sorted(component)))
        return tuple(sorted(components, key=lambda item: (item[0], len(item))))

    def statistics(self) -> GraphStatistics:
        documents = self._graph.documents()
        relations = self._graph.relations()
        self._validate_identifiers(item.document_id for item in documents)
        by_type: dict[str, int] = {}
        for document in documents:
            key = document.document_kind.value
            by_type[key] = by_type.get(key, 0) + 1
        node_count = len(documents)
        maximum_edges = node_count * (node_count - 1)
        density = len(relations) / maximum_edges if maximum_edges else 0.0
        agreement_documents = tuple(
            item
            for item in documents
            if item.document_kind is DocumentKind.AGREEMENT
        )
        return GraphStatistics(
            node_count=node_count,
            relation_count=len(relations),
            density=round(density, 12),
            orphan_document_ids=self.orphan_document_ids(),
            connected_components=self.connected_components(),
            agreement_families=tuple(
                sorted(
                    {
                        item.family
                        for item in agreement_documents
                        if item.family
                    }
                )
            ),
            agreement_version_count=sum(
                item.version_label is not None for item in agreement_documents
            ),
            documents_by_type=tuple(sorted(by_type.items())),
        )

    def _walk(
        self,
        query: NavigationQuery,
    ) -> tuple[tuple[str, ...], tuple[DocumentRelation, ...]]:
        if query.document_id is None:
            return (), ()
        allowed = set(query.relation_kinds) if query.relation_kinds else None
        visited = {query.document_id}
        queue = deque([(query.document_id, 0)])
        selected_relations: dict[str, DocumentRelation] = {}
        while queue:
            current, depth = queue.popleft()
            if depth == query.max_depth:
                continue
            for relation in self._graph.relations():
                if allowed is not None and relation.relation_kind not in allowed:
                    continue
                neighbour = None
                if (
                    query.direction in (
                        NavigationDirection.OUTGOING,
                        NavigationDirection.BOTH,
                    )
                    and relation.source_document_id == current
                ):
                    neighbour = relation.target_document_id
                elif (
                    query.direction in (
                        NavigationDirection.INCOMING,
                        NavigationDirection.BOTH,
                    )
                    and relation.target_document_id == current
                ):
                    neighbour = relation.source_document_id
                if neighbour is None:
                    continue
                selected_relations[relation.relation_id] = relation
                if neighbour not in visited:
                    visited.add(neighbour)
                    queue.append((neighbour, depth + 1))
        self._validate_identifiers(visited)
        return (
            tuple(sorted(visited - {query.document_id})),
            tuple(
                selected_relations[key] for key in sorted(selected_relations)
            ),
        )

    def _adjacency(self) -> dict[str, tuple[tuple[str, str], ...]]:
        adjacency: dict[str, list[tuple[str, str]]] = {
            item.document_id: [] for item in self._graph.documents()
        }
        for relation in self._graph.relations():
            adjacency[relation.source_document_id].append(
                (relation.target_document_id, relation.relation_id)
            )
            adjacency[relation.target_document_id].append(
                (relation.source_document_id, relation.relation_id)
            )
        return {
            key: tuple(sorted(value, key=lambda item: (item[0], item[1])))
            for key, value in sorted(adjacency.items())
        }

    @staticmethod
    def _view(document: DocumentDescriptor | None) -> NavigationDocument:
        if document is None:
            raise ValueError("document does not exist")
        return NavigationDocument(
            document_id=document.document_id,
            title=document.title,
            document_kind=document.document_kind,
            provenance=document.provenance,
            publication_date=document.publication_date,
            effective_from=document.effective_from,
            effective_to=document.effective_to,
            version=document.version_label,
            family=document.family,
            instance=document.instance,
            nature=document.nature,
            status=document.status,
        )

    @staticmethod
    def _validate_identifier(document_id: str) -> None:
        if not is_pseudonymous_id(document_id):
            raise ValueError("document_id must be pseudonymized")

    @classmethod
    def _validate_identifiers(cls, document_ids: Iterable[str]) -> None:
        for document_id in document_ids:
            cls._validate_identifier(document_id)
