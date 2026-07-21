"""Strict metadata-only input for CARSAT document synchronization."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from automation.official_knowledge.document_registry import stable_document_id


CARSAT_CONNECTOR_NAME = "carsat"
CARSAT_PROVENANCE = "carsat"


class CarsatMetadataRefusal(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CarsatMetadata:
    """Validated public metadata with no field capable of retaining content."""

    document_id: str
    canonical_url: str
    title: str
    publication_date: str | None
    category: str
    family: str
    document_type: str
    language: str
    provenance: str
    discovered_at: str
    reference: str | None = None
    metadata_only: bool = True

    def __post_init__(self) -> None:
        canonical_url = canonicalize_carsat_url(self.canonical_url)
        object.__setattr__(self, "canonical_url", canonical_url)
        expected = stable_document_id(CARSAT_CONNECTOR_NAME, canonical_url)
        if self.document_id != expected:
            raise CarsatMetadataRefusal("INCONSISTENT_DOCUMENT_ID", "Document identifier must use the common registry identity.")
        if self.metadata_only is not True:
            raise CarsatMetadataRefusal("METADATA_ONLY_REQUIRED", "Only metadata may be retained.")
        if self.provenance != CARSAT_PROVENANCE:
            raise CarsatMetadataRefusal("PROVENANCE_REQUIRED", "CARSAT provenance is mandatory.")
        for name, maximum in (("title", 500), ("category", 100), ("family", 100), ("document_type", 100), ("language", 20)):
            _validate_text(getattr(self, name), maximum)
        if self.reference is not None:
            _validate_text(self.reference, 200)
        if self.publication_date is not None:
            _validate_date(self.publication_date, "INVALID_PUBLICATION_DATE")
        _validate_date(self.discovered_at, "INVALID_DISCOVERY_DATE")

    @classmethod
    def create(
        cls,
        *,
        canonical_url: str,
        title: str,
        publication_date: str | None,
        category: str,
        family: str,
        document_type: str,
        discovered_at: str,
        language: str = "fr",
        provenance: str = CARSAT_PROVENANCE,
        reference: str | None = None,
    ) -> "CarsatMetadata":
        canonical = canonicalize_carsat_url(canonical_url)
        return cls(
            document_id=stable_document_id(CARSAT_CONNECTOR_NAME, canonical),
            canonical_url=canonical,
            title=title,
            publication_date=publication_date,
            category=category,
            family=family,
            document_type=document_type,
            language=language,
            provenance=provenance,
            discovered_at=discovered_at,
            reference=reference,
        )


def canonicalize_carsat_url(value: str) -> str:
    """Normalize a plain HTTPS URL; connector-specific domains stay registry-owned."""

    if not isinstance(value, str) or not value.strip():
        raise CarsatMetadataRefusal("INVALID_URL", "A canonical URL is required.")
    candidate = value.strip()
    match = re.fullmatch(r"https://([^/?#]+)([^?#]*)(?:\?([^#]*))?(?:#.*)?", candidate, re.IGNORECASE)
    if match is None:
        raise CarsatMetadataRefusal("HTTPS_REQUIRED", "Only plain HTTPS URLs are accepted.")
    authority, path, query = match.groups()
    host = authority.lower().rstrip(".")
    if not host or "@" in authority or ":" in authority or any(character.isspace() for character in candidate):
        raise CarsatMetadataRefusal("INVALID_URL", "Malformed canonical URL.")
    normalized_path = re.sub(r"/{2,}", "/", path or "/")
    if normalized_path != "/":
        normalized_path = normalized_path.rstrip("/")
    lowered = normalized_path.lower()
    if lowered.endswith((".pdf", "%2epdf")) or "/pdf/" in lowered:
        raise CarsatMetadataRefusal("PDF_FORBIDDEN", "PDF resources are forbidden.")
    return f"https://{host}{normalized_path}" + (f"?{query}" if query else "")


def _validate_text(value: str, maximum: int) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise CarsatMetadataRefusal("INVALID_METADATA", "Invalid bounded metadata text.")
    if "<" in value or ">" in value:
        raise CarsatMetadataRefusal("HTML_FORBIDDEN", "Raw HTML is forbidden.")


def _validate_date(value: str, code: str) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise CarsatMetadataRefusal(code, "Date must use ISO YYYY-MM-DD format.") from exc
