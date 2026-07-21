"""Abstract contract for a future metadata-only local document search provider."""

from typing import Protocol

from .career_evidence_models import DocumentSearchRequest, DocumentSearchResult


class CareerDocumentSearchProvider(Protocol):
    """Provider boundary with no implementation, storage or corpus coupling."""

    def search_ineos_agreements(self, request: DocumentSearchRequest) -> tuple[DocumentSearchResult, ...]: ...

    def search_collective_agreement(self, request: DocumentSearchRequest) -> tuple[DocumentSearchResult, ...]: ...

    def search_carsat_sources(self, request: DocumentSearchRequest) -> tuple[DocumentSearchResult, ...]: ...

    def search_c2p_sources(self, request: DocumentSearchRequest) -> tuple[DocumentSearchResult, ...]: ...

    def search_document_passages(self, request: DocumentSearchRequest) -> tuple[DocumentSearchResult, ...]: ...
