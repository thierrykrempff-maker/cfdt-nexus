"""Strict metadata-only representation for public INRS references."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date
from enum import Enum
from hashlib import sha256
from typing import Any, Mapping


INRS_CONNECTOR_NAME = "inrs"
INRS_SOURCE_NAME = "INRS"
INRS_SOURCE_DOMAIN = "www.inrs.fr"
INRS_ALLOWED_DOMAINS = frozenset({INRS_SOURCE_DOMAIN})
INRS_PROVENANCE = "inrs"
INRS_IDENTITY_QUERY_PARAMETERS = frozenset({"id", "refinrs"})


class InrsMetadataRefusal(ValueError):
    """Fail-closed refusal carrying a stable, non-sensitive error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class InrsMetadataFamily(str, Enum):
    RISQUES_CHIMIQUES = "risques_chimiques"
    ACCIDENTS_TRAVAIL = "accidents_travail"
    MALADIES_PROFESSIONNELLES = "maladies_professionnelles"
    EQUIPEMENTS_PROTECTION = "equipements_protection"
    MACHINES = "machines"
    INCENDIE_EXPLOSION = "incendie_explosion"
    TROUBLES_MUSCULOSQUELETTIQUES = "troubles_musculosquelettiques"
    RISQUES_PSYCHOSOCIAUX = "risques_psychosociaux"
    ORGANISATION_TRAVAIL = "organisation_travail"
    PREVENTION = "prevention"
    REGLEMENTATION = "reglementation"
    FORMATION = "formation"
    AUTRE = "autre"


class InrsMetadataDocumentType(str, Enum):
    BROCHURE = "brochure"
    FICHE_PRATIQUE = "fiche_pratique"
    DOSSIER_WEB = "dossier_web"
    AFFICHE = "affiche"
    OUTIL = "outil"
    GUIDE = "guide"
    ARTICLE = "article"
    VIDEO = "video"
    FORMATION = "formation"
    PUBLICATION = "publication"
    AUTRE = "autre"


@dataclass(frozen=True)
class InrsMetadata:
    """Normalized metadata; deliberately incapable of retaining document content."""

    document_id: str
    connector_name: str
    source_name: str
    source_domain: str
    canonical_url: str
    title: str
    document_type: InrsMetadataDocumentType
    category: str
    family: InrsMetadataFamily
    publication_date: str | None
    last_modified_date: str | None
    language: str
    metadata_only: bool
    discovered_at: str
    reference: str | None = None
    edition: str | None = None
    author: str | None = None
    status: str | None = None
    keywords: tuple[str, ...] = ()
    summary: str | None = None
    redirect_url: str | None = None
    provenance: str = INRS_PROVENANCE

    def __post_init__(self) -> None:
        canonical_url = canonicalize_inrs_url(self.canonical_url)
        object.__setattr__(self, "canonical_url", canonical_url)
        if self.connector_name != INRS_CONNECTOR_NAME:
            raise InrsMetadataRefusal("INVALID_CONNECTOR", "INRS connector identity is required.")
        if self.source_name != INRS_SOURCE_NAME or self.source_domain != INRS_SOURCE_DOMAIN:
            raise InrsMetadataRefusal("INVALID_SOURCE", "Official INRS source metadata is required.")
        if self.provenance != INRS_PROVENANCE:
            raise InrsMetadataRefusal("PROVENANCE_REQUIRED", "Official INRS provenance is required.")
        if self.metadata_only is not True:
            raise InrsMetadataRefusal("METADATA_ONLY_REQUIRED", "Only metadata may be retained.")
        _validate_short_text(self.title, "INVALID_TITLE", maximum=500, required=True)
        _validate_short_text(self.category, "INVALID_CATEGORY", maximum=100, required=True)
        _validate_short_text(self.language, "INVALID_LANGUAGE", maximum=20, required=True)
        for field_name in ("edition", "author", "status"):
            _validate_short_text(getattr(self, field_name), "INVALID_METADATA", maximum=200)
        _validate_short_text(self.summary, "CONTENT_FORBIDDEN", maximum=500)
        if not isinstance(self.keywords, tuple) or len(self.keywords) > 20:
            raise InrsMetadataRefusal("INVALID_KEYWORDS", "Keywords must be a bounded tuple.")
        for keyword in self.keywords:
            _validate_short_text(keyword, "INVALID_KEYWORDS", maximum=100, required=True)
        try:
            object.__setattr__(self, "family", InrsMetadataFamily(self.family))
            object.__setattr__(self, "document_type", InrsMetadataDocumentType(self.document_type))
        except (TypeError, ValueError) as exc:
            raise InrsMetadataRefusal("UNKNOWN_TAXONOMY", "Unknown INRS taxonomy value.") from exc
        for field_name in ("publication_date", "last_modified_date"):
            value = getattr(self, field_name)
            if value is not None:
                _validate_iso_date(value, "INVALID_DATE")
        _validate_iso_date(self.discovered_at, "INVALID_DISCOVERY_DATE")
        if self.redirect_url is not None:
            object.__setattr__(self, "redirect_url", canonicalize_inrs_url(self.redirect_url))
        expected_id = stable_inrs_document_id(canonical_url, self.reference)
        if self.document_id != expected_id:
            raise InrsMetadataRefusal("INCONSISTENT_DOCUMENT_ID", "Document identifier is not reproducible.")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["family"] = self.family.value
        result["document_type"] = self.document_type.value
        return result

    def to_registry_fields(self) -> dict[str, str | None]:
        """Return only fields shared with DocumentRecord, without writing anything."""

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


def stable_inrs_document_id(canonical_url: str, reference: str | None = None) -> str:
    """Create a stable identifier from the official reference, then URL as fallback."""

    normalized_reference = normalize_inrs_reference(reference)
    identity = f"reference:{normalized_reference}" if normalized_reference else f"url:{canonicalize_inrs_url(canonical_url)}"
    return sha256(f"{INRS_CONNECTOR_NAME}\n{identity}".encode("utf-8")).hexdigest()


def normalize_inrs_reference(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InrsMetadataRefusal("INVALID_REFERENCE", "INRS reference must be textual.")
    normalized = "-".join(re.findall(r"[A-Z]+|[0-9]+", value.upper()))
    if not normalized:
        raise InrsMetadataRefusal("INVALID_REFERENCE", "INRS reference is empty.")
    return normalized


def canonicalize_inrs_url(value: str) -> str:
    """Canonicalize an HTTPS URL without importing or depending on network clients."""

    if not isinstance(value, str) or not value.strip():
        raise InrsMetadataRefusal("INVALID_URL", "An INRS URL is required.")
    candidate = value.strip()
    match = re.fullmatch(r"https://([^/?#]+)([^?#]*)(?:\?([^#]*))?(?:#.*)?", candidate, re.IGNORECASE)
    if match is None:
        raise InrsMetadataRefusal("HTTPS_REQUIRED", "A plain HTTPS INRS URL is required.")
    authority, raw_path, raw_query = match.groups()
    host = authority.lower().rstrip(".")
    if host not in INRS_ALLOWED_DOMAINS or "@" in authority or ":" in authority:
        raise InrsMetadataRefusal("DOMAIN_NOT_ALLOWED", "Only explicitly allowed INRS domains are accepted.")
    if any(ord(character) < 32 or character.isspace() for character in candidate):
        raise InrsMetadataRefusal("INVALID_URL", "Whitespace and control characters are forbidden.")
    path = re.sub(r"/{2,}", "/", raw_path or "/")
    if path != "/":
        path = path.rstrip("/")
    lowered_path = path.lower()
    if lowered_path.endswith((".pdf", "%2epdf")) or "/pdf/" in lowered_path:
        raise InrsMetadataRefusal("PDF_FORBIDDEN", "PDF resources are forbidden.")
    identity_parameters: list[tuple[str, str]] = []
    for component in (raw_query or "").split("&"):
        if not component:
            continue
        key, separator, parameter_value = component.partition("=")
        if key.lower() in INRS_IDENTITY_QUERY_PARAMETERS:
            identity_parameters.append((key.lower(), parameter_value if separator else ""))
    query = "&".join(f"{key}={parameter_value}" for key, parameter_value in sorted(identity_parameters))
    return f"https://{INRS_SOURCE_DOMAIN}{path}" + (f"?{query}" if query else "")


def metadata_from_mapping(value: Mapping[str, Any]) -> InrsMetadata:
    """Validate a synthetic structured entry and reject content-shaped fields."""

    if not isinstance(value, Mapping):
        raise InrsMetadataRefusal("INVALID_ENTRY", "Metadata entry must be a mapping.")
    _reject_binary(value)
    forbidden = {"content", "full_text", "html", "pdf", "body", "raw_html"} & set(value)
    if forbidden:
        raise InrsMetadataRefusal("CONTENT_FORBIDDEN", "Document content fields are forbidden.")
    allowed = {
        "url", "title", "document_type", "category", "family", "publication_date",
        "last_modified_date", "language", "discovered_at", "reference", "edition",
        "author", "status", "keywords", "summary", "redirect_url",
    }
    unknown = set(value) - allowed
    if unknown:
        raise InrsMetadataRefusal("UNKNOWN_FIELDS", f"Unknown metadata fields: {sorted(unknown)}")
    canonical_url = canonicalize_inrs_url(value.get("url"))
    reference = value.get("reference")
    return InrsMetadata(
        document_id=stable_inrs_document_id(canonical_url, reference),
        connector_name=INRS_CONNECTOR_NAME,
        source_name=INRS_SOURCE_NAME,
        source_domain=INRS_SOURCE_DOMAIN,
        canonical_url=canonical_url,
        title=value.get("title"),
        document_type=normalize_document_type(value.get("document_type")),
        category=value.get("category") or "autre",
        family=normalize_family(value.get("family")),
        publication_date=value.get("publication_date"),
        last_modified_date=value.get("last_modified_date"),
        language=value.get("language") or "fr",
        metadata_only=True,
        discovered_at=value.get("discovered_at"),
        reference=reference,
        edition=value.get("edition"),
        author=value.get("author"),
        status=value.get("status"),
        keywords=tuple(value.get("keywords") or ()),
        summary=value.get("summary"),
        redirect_url=value.get("redirect_url"),
    )


def normalize_family(value: Any) -> InrsMetadataFamily:
    aliases = {
        "rps": InrsMetadataFamily.RISQUES_PSYCHOSOCIAUX,
        "tms": InrsMetadataFamily.TROUBLES_MUSCULOSQUELETTIQUES,
        "epi": InrsMetadataFamily.EQUIPEMENTS_PROTECTION,
        "at_mp": InrsMetadataFamily.ACCIDENTS_TRAVAIL,
    }
    if value is None or value == "":
        return InrsMetadataFamily.AUTRE
    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in aliases:
        return aliases[normalized]
    try:
        return InrsMetadataFamily(normalized)
    except ValueError:
        return InrsMetadataFamily.AUTRE


def normalize_document_type(value: Any) -> InrsMetadataDocumentType:
    aliases = {
        "fiche": InrsMetadataDocumentType.FICHE_PRATIQUE,
        "dossier": InrsMetadataDocumentType.DOSSIER_WEB,
        "poster": InrsMetadataDocumentType.AFFICHE,
    }
    if value is None or value == "":
        return InrsMetadataDocumentType.AUTRE
    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in aliases:
        return aliases[normalized]
    try:
        return InrsMetadataDocumentType(normalized)
    except ValueError as exc:
        raise InrsMetadataRefusal("UNKNOWN_DOCUMENT_TYPE", "Unknown document type.") from exc


def _validate_iso_date(value: str, code: str) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise InrsMetadataRefusal(code, "Date must use ISO YYYY-MM-DD format.") from exc


def _validate_short_text(value: Any, code: str, *, maximum: int, required: bool = False) -> None:
    if value is None and not required:
        return
    if not isinstance(value, str) or (required and not value.strip()) or len(value) > maximum:
        raise InrsMetadataRefusal(code, "Invalid bounded metadata text.")
    if "<" in value or ">" in value:
        raise InrsMetadataRefusal("HTML_FORBIDDEN", "Raw HTML is forbidden.")


def _reject_binary(value: Any) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise InrsMetadataRefusal("BINARY_FORBIDDEN", "Binary data is forbidden.")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_binary(key)
            _reject_binary(item)
    elif isinstance(value, (tuple, list, set, frozenset)):
        for item in value:
            _reject_binary(item)
