"""Immutable contracts for deterministic documentary graph navigation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any

from .ingestion_models import is_pseudonymous_id, validate_safe_metadata
from .models import DocumentKind, DocumentRelation, RelationKind


class NavigationDirection(str, Enum):
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"
    BOTH = "BOTH"


@dataclass(frozen=True, slots=True)
class NavigationQuery:
    """Exact metadata and relationship filters for local navigation."""

    document_id: str | None = None
    document_kind: DocumentKind | None = None
    date_from: str | None = None
    date_to: str | None = None
    instance: str | None = None
    status: str | None = None
    family: str | None = None
    relation_kinds: tuple[RelationKind, ...] = ()
    direction: NavigationDirection = NavigationDirection.BOTH
    max_depth: int = 1

    def __post_init__(self) -> None:
        if self.document_id is not None and not is_pseudonymous_id(
            self.document_id
        ):
            raise ValueError("document_id must be pseudonymized")
        if not isinstance(self.direction, NavigationDirection):
            raise TypeError("direction must be a NavigationDirection")
        if not 1 <= self.max_depth <= 20:
            raise ValueError("max_depth must be between 1 and 20")
        for field_name in (
            "date_from",
            "date_to",
            "instance",
            "status",
            "family",
        ):
            value = getattr(self, field_name)
            if value is not None:
                validate_safe_metadata(value, field_name)
        object.__setattr__(
            self,
            "relation_kinds",
            tuple(
                sorted(
                    set(self.relation_kinds),
                    key=lambda item: item.value,
                )
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "date_from": self.date_from,
            "date_to": self.date_to,
            "direction": self.direction.value,
            "document_id": self.document_id,
            "document_kind": (
                self.document_kind.value if self.document_kind else None
            ),
            "family": self.family,
            "instance": self.instance,
            "max_depth": self.max_depth,
            "relation_kinds": [item.value for item in self.relation_kinds],
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class NavigationDocument:
    """Safe metadata projection exposed by the navigation API."""

    document_id: str
    title: str
    document_kind: DocumentKind
    provenance: str
    publication_date: str | None
    effective_from: str | None
    effective_to: str | None
    version: str | None
    family: str | None
    instance: str | None
    nature: str | None
    status: str

    def __post_init__(self) -> None:
        if not is_pseudonymous_id(self.document_id):
            raise ValueError("document_id must be pseudonymized")
        for field_name in (
            "title",
            "provenance",
            "publication_date",
            "effective_from",
            "effective_to",
            "version",
            "family",
            "instance",
            "nature",
            "status",
        ):
            value = getattr(self, field_name)
            if value is not None:
                validate_safe_metadata(value, field_name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_kind": self.document_kind.value,
            "effective_from": self.effective_from,
            "effective_to": self.effective_to,
            "family": self.family,
            "instance": self.instance,
            "nature": self.nature,
            "provenance": self.provenance,
            "publication_date": self.publication_date,
            "status": self.status,
            "title": self.title,
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class NavigationResult:
    """Serializable result containing safe document and relation projections."""

    query: NavigationQuery
    documents: tuple[NavigationDocument, ...]
    relations: tuple[DocumentRelation, ...] = ()

    def __post_init__(self) -> None:
        for relation in self.relations:
            if not is_pseudonymous_id(relation.source_document_id):
                raise ValueError("relation source must be pseudonymized")
            if not is_pseudonymous_id(relation.target_document_id):
                raise ValueError("relation target must be pseudonymized")
            validate_safe_metadata(
                relation.provenance,
                "relation_provenance",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "documents": [item.to_dict() for item in self.documents],
            "query": self.query.to_dict(),
            "relations": [
                {
                    "confidence": relation.confidence,
                    "provenance": validate_safe_metadata(
                        relation.provenance,
                        "relation_provenance",
                    ),
                    "relation_id": relation.relation_id,
                    "relation_kind": relation.relation_kind.value,
                    "source_document_id": relation.source_document_id,
                    "target_document_id": relation.target_document_id,
                }
                for relation in self.relations
            ],
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass(frozen=True, slots=True)
class GraphPath:
    """Shortest path expressed only with pseudonymized graph identities."""

    document_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if any(not is_pseudonymous_id(item) for item in self.document_ids):
            raise ValueError("path contains a non-pseudonymized document_id")
        if any(not is_pseudonymous_id(item) for item in self.relation_ids):
            raise ValueError("path contains a non-pseudonymized relation_id")
        if self.document_ids and len(self.relation_ids) != len(self.document_ids) - 1:
            raise ValueError("path relation count is inconsistent")

    @property
    def found(self) -> bool:
        return bool(self.document_ids)

    @property
    def length(self) -> int:
        return len(self.relation_ids)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_ids": list(self.document_ids),
            "found": self.found,
            "length": self.length,
            "relation_ids": list(self.relation_ids),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass(frozen=True, slots=True)
class GraphStatistics:
    """Deterministic metadata-only graph health indicators."""

    node_count: int
    relation_count: int
    density: float
    orphan_document_ids: tuple[str, ...]
    connected_components: tuple[tuple[str, ...], ...]
    agreement_families: tuple[str, ...]
    agreement_version_count: int
    documents_by_type: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        identifiers = self.orphan_document_ids + tuple(
            item
            for component in self.connected_components
            for item in component
        )
        if any(not is_pseudonymous_id(item) for item in identifiers):
            raise ValueError("statistics contain a non-pseudonymized document_id")
        for family in self.agreement_families:
            validate_safe_metadata(family, "agreement_family")

    def to_dict(self) -> dict[str, Any]:
        return {
            "agreement_families": list(self.agreement_families),
            "agreement_version_count": self.agreement_version_count,
            "connected_components": [
                list(component) for component in self.connected_components
            ],
            "density": self.density,
            "documents_by_type": dict(self.documents_by_type),
            "node_count": self.node_count,
            "orphan_document_ids": list(self.orphan_document_ids),
            "relation_count": self.relation_count,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
