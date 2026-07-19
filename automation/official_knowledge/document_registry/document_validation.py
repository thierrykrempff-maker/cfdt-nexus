"""Generic fail-closed validation for metadata-only official documents."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Mapping
from urllib.parse import unquote, urlsplit

from .document_models import DocumentRecord, stable_document_id


_CONNECTOR_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


class DocumentValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RegistryDocumentPolicy:
    index_level: str = "METADATA_ONLY"
    cache_allowed: bool = False
    content_storage_allowed: bool = False
    text_indexing_allowed: bool = False
    local_document_copy_allowed: bool = False
    citation_required: bool = True
    provenance_required: bool = True

    def __post_init__(self) -> None:
        if self.index_level != "METADATA_ONLY":
            raise ValueError("Document Registry is METADATA_ONLY")
        if any((self.cache_allowed, self.content_storage_allowed, self.text_indexing_allowed, self.local_document_copy_allowed)):
            raise ValueError("Document Registry must not retain document content")
        if not self.citation_required or not self.provenance_required:
            raise ValueError("citation and provenance are mandatory")


DOCUMENT_REGISTRY_POLICY = RegistryDocumentPolicy()


class DocumentValidator:
    """Validate connector-specific domains through injected generic configuration."""

    def __init__(self, allowed_domains: Mapping[str, frozenset[str]]) -> None:
        normalized: dict[str, frozenset[str]] = {}
        for connector, domains in allowed_domains.items():
            if not _CONNECTOR_PATTERN.fullmatch(connector) or not domains:
                raise ValueError("invalid connector domain policy")
            clean = frozenset(domain.lower().rstrip(".") for domain in domains)
            if any(not domain or "/" in domain or ":" in domain for domain in clean):
                raise ValueError("invalid allowed domain")
            normalized[connector] = clean
        self._allowed_domains = MappingProxyType(normalized)

    def validate_new(self, document: DocumentRecord) -> None:
        self.validate(document)
        if document.document_id != stable_document_id(document.connector_name, document.canonical_url):
            raise DocumentValidationError("UNSTABLE_DOCUMENT_ID", "New document_id must match its stable metadata identity.")

    def validate(self, document: DocumentRecord) -> None:
        if not isinstance(document, DocumentRecord):
            raise TypeError("document must be a DocumentRecord")
        if not _CONNECTOR_PATTERN.fullmatch(document.connector_name):
            raise DocumentValidationError("INVALID_CONNECTOR", "Invalid connector name.")
        domains = self._allowed_domains.get(document.connector_name)
        if domains is None:
            raise DocumentValidationError("CONNECTOR_NOT_ALLOWED", "Connector has no domain policy.")
        self._validate_url(document.canonical_url, domains)
        for name, maximum in (("title", 500), ("category", 100), ("family", 100), ("document_type", 100), ("language", 20), ("provenance", 200)):
            value = getattr(document, name)
            if not isinstance(value, str) or not value.strip() or len(value) > maximum:
                raise DocumentValidationError("INVALID_METADATA", f"Invalid {name} metadata.")
            if name == "title" and ("<" in value or ">" in value):
                raise DocumentValidationError("CONTENT_FORBIDDEN", "HTML content is forbidden.")
        if not document.provenance.strip():
            raise DocumentValidationError("PROVENANCE_REQUIRED", "Provenance is mandatory.")
        for name in ("first_seen", "last_checked", "last_modified_metadata"):
            _parse_date(getattr(document, name), "INVALID_DATE")
        if document.publication_date is not None:
            _parse_date(document.publication_date, "INVALID_PUBLICATION_DATE")
        if _parse_date(document.last_checked, "INVALID_DATE") < _parse_date(document.first_seen, "INVALID_DATE"):
            raise DocumentValidationError("INVALID_TIMELINE", "last_checked precedes first_seen.")
        modified = _parse_date(document.last_modified_metadata, "INVALID_DATE")
        if not _parse_date(document.first_seen, "INVALID_DATE") <= modified <= _parse_date(document.last_checked, "INVALID_DATE"):
            raise DocumentValidationError("INVALID_TIMELINE", "last_modified_metadata is outside the observation period.")

    @staticmethod
    def _validate_url(value: str, domains: frozenset[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            raise DocumentValidationError("INVALID_URL", "Canonical URL is required.")
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as exc:
            raise DocumentValidationError("INVALID_URL", "Malformed canonical URL.") from exc
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme != "https" or not host or parsed.username or parsed.password or port is not None or parsed.fragment:
            raise DocumentValidationError("INVALID_URL", "Canonical URL must be plain HTTPS without fragment.")
        if host not in domains:
            raise DocumentValidationError("DOMAIN_NOT_ALLOWED", "Document domain is not allowed for this connector.")
        decoded = unquote(value).lower()
        if decoded.endswith(".pdf") or ".pdf?" in decoded or "/img/pdf/" in decoded:
            raise DocumentValidationError("PDF_FORBIDDEN", "PDF documents are forbidden.")


def _parse_date(value: str, code: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise DocumentValidationError(code, "Date must use ISO YYYY-MM-DD format.") from exc
