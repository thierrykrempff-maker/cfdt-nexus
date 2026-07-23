"""Public API for the metadata-only Document Intelligence Center."""

from .graph import DocumentGraph, DocumentGraphError
from .agreements_adapter import (
    INEOSAgreementMetadataAdapter,
    stable_agreement_id,
)
from .cse_memory_adapter import CSEMemoryMetadataAdapter
from .ingestion_audit import IngestionAuditExporter
from .ingestion_models import (
    AgreementMetadataInput,
    AgreementNature,
    DocumentMetadataInput,
    ExplicitDocumentLink,
    IngestionBatchResult,
    IngestionDecision,
    IngestionIssue,
    IngestionResult,
    IssueSeverity,
    MeetingMinutesMetadataInput,
    MetadataStatus,
    is_pseudonymous_id,
    validate_safe_metadata,
)
from .ingestion_service import DocumentIngestionService
from .metadata_index import MetadataIndex, MetadataQuery
from .models import (
    DocumentDescriptor,
    DocumentKind,
    DocumentRelation,
    RelationKind,
)
from .pv_linking import PVAgreementLinker
from .navigation_models import (
    GraphPath,
    GraphStatistics,
    NavigationDirection,
    NavigationDocument,
    NavigationQuery,
    NavigationResult,
)
from .navigation_service import DocumentNavigationService
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
    "AgreementMetadataInput",
    "AgreementNature",
    "CSEMemoryMetadataAdapter",
    "DocumentDescriptor",
    "DocumentGraph",
    "DocumentGraphError",
    "DocumentIngestionService",
    "DocumentKind",
    "DocumentMetadataInput",
    "DocumentNavigationService",
    "DocumentRelation",
    "DocumentSearchBackend",
    "ExplicitDocumentLink",
    "INEOSAgreementMetadataAdapter",
    "IngestionAuditExporter",
    "IngestionBatchResult",
    "IngestionDecision",
    "IngestionIssue",
    "IngestionResult",
    "IssueSeverity",
    "MeetingMinutesMetadataInput",
    "MetadataIndex",
    "MetadataQuery",
    "MetadataStatus",
    "is_pseudonymous_id",
    "validate_safe_metadata",
    "GraphPath",
    "GraphStatistics",
    "NavigationDirection",
    "NavigationDocument",
    "NavigationQuery",
    "NavigationResult",
    "PVAgreementLinker",
    "RelationKind",
    "SearchDocument",
    "SearchHit",
    "SearchProjectionBuilder",
    "SearchQuery",
    "stable_agreement_id",
]
