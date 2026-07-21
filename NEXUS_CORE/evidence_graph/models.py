"""Reference-only models for the neutral Nexus Evidence Graph."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..identifiers import ConflictId, DocumentId, EntityId, EvidenceId, FindingId
from ..periods import Period
from ..provenance import Provenance
from ..quality import ConfidenceScore


class EvidenceRelationType(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DUPLICATES = "duplicates"
    REFERENCES = "references"
    EXTENDS = "extends"
    CORROBORATES = "corroborates"
    UNKNOWN = "unknown"


class GraphNodeType(str, Enum):
    EVIDENCE = "evidence"
    FINDING = "finding"
    CONFLICT = "conflict"
    DOCUMENT = "document"


class GraphStatus(str, Enum):
    EMPTY = "empty"
    ACTIVE = "active"
    SEALED = "sealed"


GraphReference = EvidenceId | FindingId | ConflictId | DocumentId


_REFERENCE_TYPES = {
    GraphNodeType.EVIDENCE: EvidenceId,
    GraphNodeType.FINDING: FindingId,
    GraphNodeType.CONFLICT: ConflictId,
    GraphNodeType.DOCUMENT: DocumentId,
}


@dataclass(frozen=True, slots=True)
class EvidenceNode:
    """A graph node containing only a typed reference to a Core object."""

    node_id: EntityId
    node_type: GraphNodeType
    reference: GraphReference
    period: Period | None = None

    def __post_init__(self) -> None:
        expected = _REFERENCE_TYPES[self.node_type]
        if not isinstance(self.reference, expected):
            raise TypeError(f"{self.node_type.value} node requires {expected.__name__}")


@dataclass(frozen=True, slots=True)
class EvidenceRelation:
    """Generic relation attributes, independent from endpoints."""

    relation_type: EvidenceRelationType
    confidence: ConfidenceScore
    provenance: Provenance
    period: Period | None = None


@dataclass(frozen=True, slots=True)
class EvidenceEdge:
    """A directed edge with generic, non-legal relation semantics."""

    edge_id: EntityId
    origin: EntityId
    destination: EntityId
    relation_type: EvidenceRelationType
    confidence: ConfidenceScore
    provenance: Provenance
    period: Period | None = None

    @classmethod
    def from_relation(
        cls,
        edge_id: EntityId,
        origin: EntityId,
        destination: EntityId,
        relation: EvidenceRelation,
    ) -> "EvidenceEdge":
        return cls(
            edge_id=edge_id,
            origin=origin,
            destination=destination,
            relation_type=relation.relation_type,
            confidence=relation.confidence,
            provenance=relation.provenance,
            period=relation.period,
        )


@dataclass(frozen=True, slots=True)
class EvidenceLink:
    """A minimal adjacency projection that never copies referenced data."""

    edge_id: EntityId
    origin: EntityId
    destination: EntityId
    relation_type: EvidenceRelationType


@dataclass(frozen=True, slots=True)
class EvidenceCluster:
    """A named technical grouping of graph node identifiers."""

    cluster_id: EntityId
    node_ids: tuple[EntityId, ...]
    label_code: str

    def __post_init__(self) -> None:
        if len(set(self.node_ids)) != len(self.node_ids):
            raise ValueError("cluster node identifiers must be unique")
        if not self.label_code or not self.label_code.replace("_", "").isalnum():
            raise ValueError("cluster label must be a stable technical code")


@dataclass(frozen=True, slots=True)
class GraphStatistics:
    node_count: int
    edge_count: int
    cluster_count: int
    nodes_by_type: tuple[tuple[GraphNodeType, int], ...]
    edges_by_relation: tuple[tuple[EvidenceRelationType, int], ...]
