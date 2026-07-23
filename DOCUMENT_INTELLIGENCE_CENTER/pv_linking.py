"""Link CSE/CSSCT minutes to agreements using explicit metadata references."""

from __future__ import annotations

from typing import Iterable

from .models import (
    DocumentDescriptor,
    DocumentKind,
    DocumentRelation,
    RelationKind,
)


class PVAgreementLinker:
    """Create deterministic links without reading or analysing document text."""

    _MINUTES_KINDS = (DocumentKind.CSE_MINUTES, DocumentKind.CSSCT_MINUTES)

    def link(
        self,
        minutes: DocumentDescriptor,
        agreements: Iterable[DocumentDescriptor],
    ) -> tuple[DocumentRelation, ...]:
        if minutes.document_kind not in self._MINUTES_KINDS:
            raise ValueError("minutes must be a CSE or CSSCT minutes document")
        agreement_items = tuple(
            item
            for item in agreements
            if item.document_kind is DocumentKind.AGREEMENT
        )
        by_id = {item.document_id: item for item in agreement_items}
        by_url = {
            item.canonical_url: item
            for item in agreement_items
            if item.canonical_url is not None
        }
        matched_ids = {
            reference
            for reference in minutes.referenced_document_ids
            if reference in by_id
        }
        matched_ids.update(
            by_url[url].document_id
            for url in minutes.referenced_canonical_urls
            if url in by_url
        )
        return tuple(
            DocumentRelation(
                source_document_id=minutes.document_id,
                target_document_id=document_id,
                relation_kind=RelationKind.REFERENCES,
                provenance=minutes.provenance,
                confidence=1.0,
            )
            for document_id in sorted(matched_ids)
        )
