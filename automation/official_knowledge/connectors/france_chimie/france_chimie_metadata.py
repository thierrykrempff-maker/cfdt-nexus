"""Strict validation of locally injected France Chimie metadata."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Mapping

from automation.official_knowledge.document_registry import stable_document_id

from .france_chimie_models import FranceChimieDocumentType, FranceChimieResourceFamily


FRANCE_CHIMIE_CONNECTOR_NAME = "france_chimie"
FRANCE_CHIMIE_PROVENANCE = "france_chimie"
DEFAULT_METADATA_LIMIT = 50
MAX_METADATA_LIMIT = 100


class FranceChimieMetadataRefusal(ValueError):
    """Fail-closed refusal with a stable and non-sensitive code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class FranceChimieMetadata:
    """Normalized metadata with no field capable of retaining content."""

    document_id: str
    connector_name: str
    canonical_url: str
    title: str
    publication_date: str | None
    category: str
    family: FranceChimieResourceFamily
    document_type: FranceChimieDocumentType
    language: str
    provenance: str
    discovered_at: str
    reference: str | None = None
    metadata_only: bool = True

    def __post_init__(self) -> None:
        if self.connector_name != FRANCE_CHIMIE_CONNECTOR_NAME:
            raise FranceChimieMetadataRefusal("INVALID_CONNECTOR", "France Chimie connector identity is required.")
        if self.metadata_only is not True:
            raise FranceChimieMetadataRefusal("METADATA_ONLY_REQUIRED", "Only metadata may be retained.")
        if self.provenance != FRANCE_CHIMIE_PROVENANCE:
            raise FranceChimieMetadataRefusal("PROVENANCE_REQUIRED", "France Chimie provenance is mandatory.")
        if not isinstance(self.family, FranceChimieResourceFamily):
            raise FranceChimieMetadataRefusal("UNKNOWN_FAMILY", "Unknown France Chimie resource family.")
        if not isinstance(self.document_type, FranceChimieDocumentType):
            raise FranceChimieMetadataRefusal("UNKNOWN_DOCUMENT_TYPE", "Unknown France Chimie document type.")
        for value, maximum in (
            (self.title, 500),
            (self.category, 100),
            (self.language, 20),
        ):
            _validate_text(value, maximum)
        if self.reference is not None:
            _validate_text(self.reference, 200)
        if self.publication_date is not None:
            _validate_date(self.publication_date, "INVALID_PUBLICATION_DATE")
        _validate_date(self.discovered_at, "INVALID_DISCOVERY_DATE")
        expected = stable_document_id(FRANCE_CHIMIE_CONNECTOR_NAME, self.canonical_url)
        if self.document_id != expected:
            raise FranceChimieMetadataRefusal(
                "INCONSISTENT_DOCUMENT_ID",
                "Document identifier must use the common registry identity.",
            )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["family"] = self.family.value
        value["document_type"] = self.document_type.value
        return value

    def to_registry_fields(self) -> dict[str, str | None]:
        return {
            "document_id": self.document_id,
            "connector_name": self.connector_name,
            "canonical_url": self.canonical_url,
            "title": self.title,
            "category": self.category,
            "family": self.family.value,
            "document_type": self.document_type.value,
            "publication_date": self.publication_date,
            "language": self.language,
            "provenance": self.provenance,
        }


def metadata_from_mapping(
    value: Mapping[str, Any],
    *,
    allowed_domains: frozenset[str],
) -> FranceChimieMetadata:
    """Normalize one local mapping; no transport or registry operation is performed."""

    if not isinstance(value, Mapping):
        raise FranceChimieMetadataRefusal("INVALID_ENTRY", "Metadata entry must be a mapping.")
    _reject_binary(value)
    forbidden = {"attachment", "body", "content", "excerpt", "full_text", "html", "pdf", "raw_html", "text"}
    if forbidden & set(value):
        raise FranceChimieMetadataRefusal("CONTENT_FORBIDDEN", "Document content fields are forbidden.")
    allowed = {
        "url",
        "title",
        "publication_date",
        "category",
        "family",
        "document_type",
        "language",
        "discovered_at",
        "reference",
    }
    unknown = set(value) - allowed
    if unknown:
        raise FranceChimieMetadataRefusal("UNKNOWN_FIELDS", f"Unknown metadata fields: {sorted(unknown)}")
    canonical_url = canonicalize_france_chimie_url(value.get("url"), allowed_domains=allowed_domains)
    family = _enum_value(FranceChimieResourceFamily, value.get("family"), "UNKNOWN_FAMILY")
    document_type = _enum_value(FranceChimieDocumentType, value.get("document_type"), "UNKNOWN_DOCUMENT_TYPE")
    return FranceChimieMetadata(
        document_id=stable_document_id(FRANCE_CHIMIE_CONNECTOR_NAME, canonical_url),
        connector_name=FRANCE_CHIMIE_CONNECTOR_NAME,
        canonical_url=canonical_url,
        title=value.get("title"),
        publication_date=value.get("publication_date"),
        category=value.get("category"),
        family=family,
        document_type=document_type,
        language=value.get("language") or "fr",
        provenance=FRANCE_CHIMIE_PROVENANCE,
        discovered_at=value.get("discovered_at"),
        reference=value.get("reference"),
    )


def normalize_injected_metadata(
    entries: tuple[Mapping[str, Any], ...],
    *,
    allowed_domains: frozenset[str],
    limit: int = DEFAULT_METADATA_LIMIT,
) -> tuple[FranceChimieMetadata, ...]:
    """Validate a bounded local batch and return a deterministic immutable result."""

    if not isinstance(entries, tuple):
        raise FranceChimieMetadataRefusal("INVALID_BATCH", "Metadata entries must be an immutable tuple.")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_METADATA_LIMIT:
        raise FranceChimieMetadataRefusal("INVALID_LIMIT", "Metadata limit must be between 1 and 100.")
    if len(entries) > limit:
        raise FranceChimieMetadataRefusal("LIMIT_EXCEEDED", "Metadata limit exceeded.")
    documents: dict[str, FranceChimieMetadata] = {}
    for entry in entries:
        document = metadata_from_mapping(entry, allowed_domains=allowed_domains)
        previous = documents.get(document.document_id)
        if previous is not None and previous != document:
            raise FranceChimieMetadataRefusal(
                "DUPLICATE_CONFLICT",
                "Conflicting metadata share one document identity.",
            )
        documents[document.document_id] = document
    return tuple(sorted(documents.values(), key=lambda item: (item.canonical_url, item.document_id)))


def canonicalize_france_chimie_url(value: Any, *, allowed_domains: frozenset[str]) -> str:
    """Canonicalize an injected HTTPS URL against an explicit inactive-by-default policy."""

    domains = _normalize_domains(allowed_domains)
    if not domains:
        raise FranceChimieMetadataRefusal("DOMAIN_POLICY_INACTIVE", "No France Chimie domain is activated.")
    if not isinstance(value, str) or not value.strip():
        raise FranceChimieMetadataRefusal("INVALID_URL", "A canonical URL is required.")
    candidate = value.strip()
    if "#" in candidate:
        raise FranceChimieMetadataRefusal("INVALID_URL", "URL fragments are forbidden.")
    match = re.fullmatch(r"https://([^/?#]+)([^?#]*)(?:\?([^#]*))?", candidate, re.IGNORECASE)
    if match is None:
        raise FranceChimieMetadataRefusal("HTTPS_REQUIRED", "Only plain HTTPS URLs are accepted.")
    authority, raw_path, raw_query = match.groups()
    host = authority.lower().rstrip(".")
    if host not in domains:
        raise FranceChimieMetadataRefusal("DOMAIN_NOT_ALLOWED", "The source domain is not explicitly allowed.")
    if "@" in authority or ":" in authority or any(character.isspace() or ord(character) < 32 for character in candidate):
        raise FranceChimieMetadataRefusal("INVALID_URL", "Malformed canonical URL.")
    path = re.sub(r"/{2,}", "/", raw_path or "/")
    if path != "/":
        path = path.rstrip("/")
    lowered = (path + "?" + (raw_query or "")).lower()
    if lowered.endswith((".pdf", "%2epdf")) or ".pdf?" in lowered or "/pdf/" in lowered:
        raise FranceChimieMetadataRefusal("PDF_FORBIDDEN", "PDF resources are forbidden.")
    query = "&".join(sorted(part for part in (raw_query or "").split("&") if part))
    return f"https://{host}{path}" + (f"?{query}" if query else "")


def _normalize_domains(value: frozenset[str]) -> frozenset[str]:
    if not isinstance(value, frozenset):
        raise FranceChimieMetadataRefusal("INVALID_DOMAIN_POLICY", "Allowed domains must be a frozenset.")
    normalized = frozenset(item.lower().rstrip(".") for item in value if isinstance(item, str) and item.strip())
    if len(normalized) != len(value) or any("/" in item or ":" in item for item in normalized):
        raise FranceChimieMetadataRefusal("INVALID_DOMAIN_POLICY", "Allowed domains are invalid.")
    return normalized


def _enum_value(enum_type, value: Any, code: str):
    try:
        return enum_type(str(value).strip().lower())
    except (TypeError, ValueError) as exc:
        raise FranceChimieMetadataRefusal(code, "Unknown metadata taxonomy value.") from exc


def _validate_text(value: Any, maximum: int) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise FranceChimieMetadataRefusal("INVALID_METADATA", "Invalid bounded metadata text.")
    if "<" in value or ">" in value:
        raise FranceChimieMetadataRefusal("HTML_FORBIDDEN", "Raw HTML is forbidden.")


def _validate_date(value: str, code: str) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise FranceChimieMetadataRefusal(code, "Date must use ISO YYYY-MM-DD format.") from exc


def _reject_binary(value: Any) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise FranceChimieMetadataRefusal("BINARY_FORBIDDEN", "Binary data is forbidden.")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_binary(key)
            _reject_binary(item)
    elif isinstance(value, (tuple, list, set, frozenset)):
        for item in value:
            _reject_binary(item)
