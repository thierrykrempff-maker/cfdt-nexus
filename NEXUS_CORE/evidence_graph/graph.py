"""Small immutable operations for a reference-only Evidence Graph."""

from __future__ import annotations

from dataclasses import dataclass, replace

from ..identifiers import EntityId
from ..periods import Period
from ..serialization import to_json
from .models import (
    EvidenceCluster,
    EvidenceEdge,
    EvidenceLink,
    EvidenceNode,
    EvidenceRelationType,
    GraphNodeType,
    GraphStatistics,
    GraphStatus,
)


@dataclass(frozen=True, slots=True)
class EvidenceGraph:
    graph_id: EntityId
    status: GraphStatus = GraphStatus.EMPTY
    nodes: tuple[EvidenceNode, ...] = ()
    edges: tuple[EvidenceEdge, ...] = ()
    clusters: tuple[EvidenceCluster, ...] = ()
    schema_version: str = "1.0"

    @classmethod
    def empty(cls, graph_id: EntityId) -> "EvidenceGraph":
        return cls(graph_id=graph_id)

    def add_node(self, node: EvidenceNode) -> "EvidenceGraph":
        self._ensure_mutable()
        existing = self.find_node(node.node_id)
        if existing == node:
            return self
        if existing is not None:
            raise ValueError("node identifier already refers to another node")
        return replace(self, status=GraphStatus.ACTIVE, nodes=self.nodes + (node,))

    def add_relation(self, edge: EvidenceEdge) -> "EvidenceGraph":
        self._ensure_mutable()
        if self.find_node(edge.origin) is None or self.find_node(edge.destination) is None:
            raise ValueError("edge endpoints must reference existing nodes")
        existing = next((item for item in self.edges if item.edge_id == edge.edge_id), None)
        if existing == edge:
            return self
        if existing is not None:
            raise ValueError("edge identifier already refers to another edge")
        return replace(self, status=GraphStatus.ACTIVE, edges=self.edges + (edge,))

    def add_cluster(self, cluster: EvidenceCluster) -> "EvidenceGraph":
        self._ensure_mutable()
        known = {node.node_id for node in self.nodes}
        if not set(cluster.node_ids).issubset(known):
            raise ValueError("cluster must reference existing nodes")
        existing = next(
            (item for item in self.clusters if item.cluster_id == cluster.cluster_id), None
        )
        if existing == cluster:
            return self
        if existing is not None:
            raise ValueError("cluster identifier already exists")
        return replace(self, status=GraphStatus.ACTIVE, clusters=self.clusters + (cluster,))

    def seal(self) -> "EvidenceGraph":
        return replace(self, status=GraphStatus.SEALED)

    def find_node(self, node_id: EntityId) -> EvidenceNode | None:
        return next((node for node in self.nodes if node.node_id == node_id), None)

    def find_by_type(self, node_type: GraphNodeType) -> tuple[EvidenceNode, ...]:
        return tuple(node for node in self.nodes if node.node_type is node_type)

    def find_by_period(self, period: Period) -> tuple[EvidenceNode, ...]:
        return tuple(
            node
            for node in self.nodes
            if node.period is not None and node.period.overlaps(period)
        )

    def links(self) -> tuple[EvidenceLink, ...]:
        return tuple(
            EvidenceLink(edge.edge_id, edge.origin, edge.destination, edge.relation_type)
            for edge in self.edges
        )

    def traverse(self, start: EntityId, max_depth: int = 1) -> tuple[EvidenceNode, ...]:
        if max_depth < 0:
            raise ValueError("max_depth must be non-negative")
        first = self.find_node(start)
        if first is None:
            return ()
        visited = {start}
        ordered = [first]
        frontier = [start]
        for _ in range(max_depth):
            next_ids = sorted(
                {
                    edge.destination
                    for edge in self.edges
                    if edge.origin in frontier and edge.destination not in visited
                },
                key=lambda identifier: identifier.value,
            )
            if not next_ids:
                break
            visited.update(next_ids)
            ordered.extend(self.find_node(identifier) for identifier in next_ids)
            frontier = next_ids
        return tuple(node for node in ordered if node is not None)

    def statistics(self) -> GraphStatistics:
        node_counts = tuple(
            (node_type, len(self.find_by_type(node_type))) for node_type in GraphNodeType
        )
        relation_counts = tuple(
            (
                relation_type,
                sum(edge.relation_type is relation_type for edge in self.edges),
            )
            for relation_type in EvidenceRelationType
        )
        return GraphStatistics(
            node_count=len(self.nodes),
            edge_count=len(self.edges),
            cluster_count=len(self.clusters),
            nodes_by_type=node_counts,
            edges_by_relation=relation_counts,
        )

    def export_json(self) -> str:
        return to_json(self)

    def _ensure_mutable(self) -> None:
        if self.status is GraphStatus.SEALED:
            raise ValueError("sealed graph cannot be extended")
