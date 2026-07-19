"""Public API for the connector-independent official Document Registry."""

from .document_models import ChangeKind, DocumentChange, DocumentRecord, DocumentStatus, stable_document_id
from .document_registry import DocumentNotFoundError, DocumentRegistry, DuplicateDocumentError
from .document_validation import DOCUMENT_REGISTRY_POLICY, DocumentValidationError, DocumentValidator, RegistryDocumentPolicy
from .registry_storage import DocumentStorage, JsonDocumentStorage

__all__ = (
    "ChangeKind", "DOCUMENT_REGISTRY_POLICY", "DocumentChange", "DocumentNotFoundError",
    "DocumentRecord", "DocumentRegistry", "DocumentStatus", "DocumentStorage",
    "DocumentValidationError", "DocumentValidator", "DuplicateDocumentError",
    "JsonDocumentStorage", "RegistryDocumentPolicy", "stable_document_id",
)
