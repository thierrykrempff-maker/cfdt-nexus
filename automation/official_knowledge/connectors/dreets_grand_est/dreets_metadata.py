"""Strict public-metadata contract for DREETS Grand Est LOT 3A."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from urllib.parse import unquote, urlsplit, urlunsplit

from .dreets_access_review import CONSULTED_DOMAINS
from .dreets_catalog import DOMAIN_FAMILIES
from .dreets_models import CONTENT_CATEGORIES


ALLOWED_DREETS_DOMAINS = frozenset(CONSULTED_DOMAINS)
ALLOWED_METADATA_MIME_TYPES = frozenset({"text/html", "application/rss+xml", "application/atom+xml"})
DREETS_PROVENANCE = "dreets_grand_est"


class DreetsMetadataRefusal(ValueError):
    """Explicit fail-closed refusal with a stable, safe code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class DreetsDocumentPolicy:
    """Non-negotiable documentary policy for LOT 3A."""

    index_level: str = "METADATA_ONLY"
    cache_allowed: bool = False
    text_indexing_allowed: bool = False
    local_copy_allowed: bool = False
    full_text_allowed: bool = False
    excerpts_allowed: bool = False
    citation_required: bool = True
    provenance_required: bool = True

    def __post_init__(self) -> None:
        if self.index_level != "METADATA_ONLY":
            raise ValueError("LOT 3A requires METADATA_ONLY")
        if any((self.cache_allowed, self.text_indexing_allowed, self.local_copy_allowed, self.full_text_allowed, self.excerpts_allowed)):
            raise ValueError("LOT 3A forbids content retention")
        if not self.citation_required or not self.provenance_required:
            raise ValueError("citation and provenance are mandatory")


LOT_3A_DOCUMENT_POLICY = DreetsDocumentPolicy()


@dataclass(frozen=True)
class DreetsMetadata:
    """The complete and exclusive metadata retained for one public document."""

    canonical_url: str
    title: str
    date: str | None
    category: str
    family: str
    document_type: str
    provenance: str
    language: str
    discovered_on: str

    def __post_init__(self) -> None:
        canonical = canonicalize_public_url(self.canonical_url)
        object.__setattr__(self, "canonical_url", canonical)
        _validate_short_text(self.title, "title", 500)
        if "<" in self.title or ">" in self.title:
            raise DreetsMetadataRefusal("INVALID_TITLE", "Title must be plain metadata.")
        if self.date is not None:
            _validate_iso_date(self.date, "INVALID_DOCUMENT_DATE")
        if self.category not in CONTENT_CATEGORIES:
            raise DreetsMetadataRefusal("INVALID_CATEGORY", "Unknown document category.")
        if self.family not in DOMAIN_FAMILIES:
            raise DreetsMetadataRefusal("INVALID_FAMILY", "Unknown DREETS family.")
        _validate_short_text(self.document_type, "document_type", 100)
        if self.provenance != DREETS_PROVENANCE:
            raise DreetsMetadataRefusal("INVALID_PROVENANCE", "Official provenance is mandatory.")
        if self.language != "fr":
            raise DreetsMetadataRefusal("INVALID_LANGUAGE", "Only declared French metadata is accepted.")
        _validate_iso_date(self.discovered_on, "INVALID_DISCOVERY_DATE")

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


def canonicalize_public_url(value: str) -> str:
    """Validate and canonicalize an allowed HTTPS metadata URL."""
    if not isinstance(value, str) or not value.strip():
        raise DreetsMetadataRefusal("INVALID_URL", "A public URL is required.")
    try:
        parsed = urlsplit(value.strip())
        port = parsed.port
    except ValueError as exc:
        raise DreetsMetadataRefusal("INVALID_URL", "Malformed public URL.") from exc
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme.lower() != "https" or not host or parsed.username or parsed.password or port is not None:
        raise DreetsMetadataRefusal("INVALID_URL", "Only plain HTTPS public URLs are accepted.")
    if host not in ALLOWED_DREETS_DOMAINS:
        raise DreetsMetadataRefusal("DOMAIN_NOT_ALLOWED", "Domain was not approved by LOT 2A/2B.")
    if _looks_like_pdf(value):
        raise DreetsMetadataRefusal("PDF_FORBIDDEN", "PDF discovery is forbidden in LOT 3A.")
    path = parsed.path or "/"
    return urlunsplit(("https", host, path, parsed.query, ""))


def validate_metadata_mime_type(value: str) -> str:
    if not isinstance(value, str):
        raise DreetsMetadataRefusal("MIME_NOT_ALLOWED", "A validated MIME type is required.")
    normalized = value.split(";", 1)[0].strip().lower()
    if normalized == "application/pdf":
        raise DreetsMetadataRefusal("PDF_FORBIDDEN", "PDF discovery is forbidden in LOT 3A.")
    if normalized not in ALLOWED_METADATA_MIME_TYPES:
        raise DreetsMetadataRefusal("MIME_NOT_ALLOWED", "MIME type is not allowed for metadata discovery.")
    return normalized


def _looks_like_pdf(value: str) -> bool:
    decoded = unquote(value).lower()
    return decoded.endswith(".pdf") or ".pdf?" in decoded or "/img/pdf/" in decoded


def _validate_iso_date(value: str, code: str) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise DreetsMetadataRefusal(code, "Date must use ISO YYYY-MM-DD format.") from exc


def _validate_short_text(value: str, name: str, maximum: int) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise DreetsMetadataRefusal("INVALID_METADATA", f"{name} is invalid.")
