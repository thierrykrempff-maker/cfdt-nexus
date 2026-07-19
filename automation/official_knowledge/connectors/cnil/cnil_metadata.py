"""Strict, content-free metadata contract for the official CNIL connector."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from enum import StrEnum
from urllib.parse import unquote, urlsplit, urlunsplit


CNIL_CONNECTOR_NAME = "cnil"
CNIL_PROVENANCE = "cnil"
CNIL_CANONICAL_DOMAIN = "cnil.fr"
CNIL_DOMAIN_ALIASES = frozenset({"cnil.fr", "www.cnil.fr"})
CNIL_METADATA_MIME_TYPES = frozenset({
    "text/html",
    "application/rss+xml",
    "application/atom+xml",
})


class CnilMetadataRefusal(ValueError):
    """Fail-closed refusal with a deterministic, non-sensitive code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class CnilTaxonomy(StrEnum):
    ACTUALITE = "actualite"
    DELIBERATION = "deliberation"
    RECOMMANDATION = "recommandation"
    GUIDE = "guide"
    FICHE_PRATIQUE = "fiche_pratique"
    SANCTION = "sanction"
    REFERENTIEL = "referentiel"
    FAQ = "faq"
    AUTRE_PUBLICATION_PUBLIQUE = "autre_publication_publique"


@dataclass(frozen=True)
class CnilMetadata:
    """Exclusive metadata retained for one public CNIL resource."""

    canonical_url: str
    title: str
    publication_date: str | None
    category: CnilTaxonomy
    family: CnilTaxonomy
    document_type: CnilTaxonomy
    provenance: str
    language: str
    discovered_at: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "canonical_url", canonicalize_cnil_url(self.canonical_url))
        _validate_title(self.title)
        if self.publication_date is not None:
            _validate_iso_date(self.publication_date, "INVALID_PUBLICATION_DATE")
        for name in ("category", "family", "document_type"):
            value = getattr(self, name)
            try:
                normalized = CnilTaxonomy(value)
            except (TypeError, ValueError) as exc:
                raise CnilMetadataRefusal("UNKNOWN_TAXONOMY", f"Unknown {name}.") from exc
            object.__setattr__(self, name, normalized)
        if self.provenance != CNIL_PROVENANCE:
            raise CnilMetadataRefusal("PROVENANCE_REQUIRED", "Official CNIL provenance is mandatory.")
        if self.language != "fr":
            raise CnilMetadataRefusal("LANGUAGE_REQUIRED", "Declared French metadata is mandatory.")
        _validate_iso_date(self.discovered_at, "INVALID_DISCOVERY_DATE")

    def to_dict(self) -> dict[str, str | None]:
        value = asdict(self)
        value["category"] = self.category.value
        value["family"] = self.family.value
        value["document_type"] = self.document_type.value
        return value


def canonicalize_cnil_url(value: str) -> str:
    """Accept the exact official host and its www alias, canonicalized without www."""

    if not isinstance(value, str) or not value.strip():
        raise CnilMetadataRefusal("INVALID_URL", "A CNIL URL is required.")
    try:
        parsed = urlsplit(value.strip())
        port = parsed.port
    except ValueError as exc:
        raise CnilMetadataRefusal("INVALID_URL", "Malformed CNIL URL.") from exc
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme.lower() != "https" or not host:
        raise CnilMetadataRefusal("HTTPS_REQUIRED", "Only HTTPS CNIL URLs are accepted.")
    if parsed.username or parsed.password or port is not None or parsed.fragment:
        raise CnilMetadataRefusal("INVALID_URL", "Credentials, custom ports and fragments are forbidden.")
    if host not in CNIL_DOMAIN_ALIASES:
        raise CnilMetadataRefusal("DOMAIN_NOT_ALLOWED", "Only cnil.fr and its exact www alias are allowed.")
    if _looks_like_pdf(value):
        raise CnilMetadataRefusal("PDF_FORBIDDEN", "PDF resources are forbidden.")
    return urlunsplit(("https", CNIL_CANONICAL_DOMAIN, parsed.path or "/", parsed.query, ""))


def validate_cnil_mime_type(value: str) -> str:
    if not isinstance(value, str):
        raise CnilMetadataRefusal("MIME_NOT_ALLOWED", "A MIME type is required.")
    normalized = value.split(";", 1)[0].strip().lower()
    if normalized == "application/pdf":
        raise CnilMetadataRefusal("PDF_FORBIDDEN", "PDF resources are forbidden.")
    if normalized not in CNIL_METADATA_MIME_TYPES:
        raise CnilMetadataRefusal("MIME_NOT_ALLOWED", "MIME type is not allowed.")
    return normalized


def _looks_like_pdf(value: str) -> bool:
    decoded = unquote(value).lower()
    return decoded.endswith(".pdf") or ".pdf?" in decoded or "/pdf/" in decoded


def _validate_title(value: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 500:
        raise CnilMetadataRefusal("INVALID_TITLE", "A short title is required.")
    if "<" in value or ">" in value:
        raise CnilMetadataRefusal("HTML_FORBIDDEN", "HTML is forbidden in metadata titles.")


def _validate_iso_date(value: str, code: str) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise CnilMetadataRefusal(code, "Date must use ISO YYYY-MM-DD format.") from exc
