"""Public API for the metadata-only Document Intelligence Center."""

from .graph import DocumentGraph, DocumentGraphError
from .models import (
    DocumentDescriptor,
    DocumentKind,
    DocumentRelation,
    RelationKind,
)
from .pv_linking import PVAgreementLinker
from .search_contracts import (
    DocumentSearchBackend,
    SearchDocument,
    SearchHit,
    SearchProjectionBuilder,
    SearchQuery,
)
from .versioning import AgreementVersionManager, AgreementVersionReport

__all__ = [
    "AgreementVersionManager",
    "AgreementVersionReport",
    "DocumentDescriptor",
    "DocumentGraph",
    "DocumentGraphError",
    "DocumentKind",
    "DocumentRelation",
    "DocumentSearchBackend",
    "PVAgreementLinker",
    "RelationKind",
    "SearchDocument",
    "SearchHit",
    "SearchProjectionBuilder",
    "SearchQuery",
]
