"""Deterministic local index over documentary metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import DocumentDescriptor, DocumentKind


@dataclass(frozen=True, slots=True)
class MetadataQuery:
    document_id: str | None = None
    document_kind: DocumentKind | None = None
    date_from: str | None = None
    date_to: str | None = None
    instance: str | None = None
    nature: str | None = None
    agreement_reference: str | None = None
    family: str | None = None
    status: str | None = None
    version: str | None = None


class MetadataIndex:
    """Search descriptors using exact metadata and ISO date ranges only."""

    def __init__(self, documents: Iterable[DocumentDescriptor] = ()) -> None:
        self._documents = {item.document_id: item for item in documents}

    def replace_all(self, documents: Iterable[DocumentDescriptor]) -> None:
        self._documents = {item.document_id: item for item in documents}

    def find(self, query: MetadataQuery) -> tuple[DocumentDescriptor, ...]:
        def matches(document: DocumentDescriptor) -> bool:
            date = document.publication_date
            return all(
                (
                    query.document_id is None
                    or document.document_id == query.document_id,
                    query.document_kind is None
                    or document.document_kind is query.document_kind,
                    query.date_from is None
                    or (date is not None and date >= query.date_from),
                    query.date_to is None
                    or (date is not None and date <= query.date_to),
                    query.instance is None or document.instance == query.instance,
                    query.nature is None or document.nature == query.nature,
                    query.agreement_reference is None
                    or document.agreement_reference == query.agreement_reference,
                    query.family is None or document.family == query.family,
                    query.status is None
                    or document.status == query.status.upper(),
                    query.version is None
                    or document.version_label == query.version,
                )
            )

        return tuple(
            document
            for document in sorted(
                self._documents.values(),
                key=lambda item: item.document_id,
            )
            if matches(document)
        )

    def deduplication_key(self, document: DocumentDescriptor) -> tuple[str, ...]:
        return (
            document.document_kind.value,
            document.agreement_reference or "",
            document.publication_date or "",
            document.instance or "",
            document.nature or "",
            document.family or "",
            document.version_label or "",
            document.status,
        )

    def find_duplicate(
        self,
        candidate: DocumentDescriptor,
    ) -> DocumentDescriptor | None:
        key = self.deduplication_key(candidate)
        if not any(key[1:]):
            return None
        return next(
            (
                item
                for item in self._documents.values()
                if item.document_id != candidate.document_id
                and self.deduplication_key(item) == key
            ),
            None,
        )
