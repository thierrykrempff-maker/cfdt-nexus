"""Immutable, offline record of the limited official LOT 2B access review.

This module contains observations only.  It performs no network operation and
does not grant a connector permission to discover, fetch, cache or synchronize.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .dreets_catalog import ACCESS_STUDY, OFFICIAL_DOMAIN

REVIEW_DATE = "2026-07-16"
CONSULTED_DOMAINS = (OFFICIAL_DOMAIN, "dreets.gouv.fr")
LOGICAL_REQUEST_COUNT = 18
NETWORK_DISABLED_BY_DEFAULT = True


@dataclass(frozen=True)
class Evidence:
    subject: str
    status: str
    official_uri: str
    note: str


@dataclass(frozen=True)
class DocumentSample:
    url: str
    title: str
    date: str | None
    family: str
    document_type: str

    def __post_init__(self) -> None:
        if not self.url.startswith("https://grand-est.dreets.gouv.fr/"):
            raise ValueError("sample must remain on the reviewed official domain")
        if not self.title or not self.family or not self.document_type:
            raise ValueError("sample metadata is incomplete")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


EVIDENCE = (
    Evidence("rss", "published_link_payload_unverified", "https://grand-est.dreets.gouv.fr/spip.php?page=backend", "RSS link is exposed in the official footer; payload parsing was not established."),
    Evidence("atom", "not_identified_in_limited_review", "https://grand-est.dreets.gouv.fr/", "No Atom link was identified; this is not proof of absence."),
    Evidence("html_site_plan", "published_link_observed", "https://grand-est.dreets.gouv.fr/spip.php?page=plan", "SPIP HTML site plan; not an XML sitemap."),
    Evidence("xml_sitemap", "not_identified_in_limited_review", "https://grand-est.dreets.gouv.fr/", "No XML sitemap was established."),
    Evidence("public_api", "not_identified_in_limited_review", "https://grand-est.dreets.gouv.fr/", "No API, OpenAPI or developer documentation was identified."),
    Evidence("legal_terms", "officially_observed", "https://dreets.gouv.fr/Mentions-legales", "Reuse rules distinguish official documents from other copyrighted editorial content."),
)

PAGE_STRUCTURE = {
    "cms": "SPIP",
    "pagination": "observed",
    "categories": "observed",
    "publication_date": "observed",
    "update_date": "observed_on_articles",
    "author": "not_consistently_observed",
    "canonical_tag": "not_verified_by_review_tool",
    "metadata": "title_category_dates_observed",
}

DOCUMENT_POLICY = {
    "index_level": "METADATA_ONLY",
    "cache_allowed": False,
    "full_text_allowed": False,
    "extracts_retained": False,
    "citation_required": True,
    "provenance_required": True,
    "license_review": "required_per_document_category",
    "official_documents": "reuse_observed_with_clear_author_source_and_original_link",
    "other_editorial_content": "permission_required_before_reproduction",
}

ARCHITECTURE_COMPARISON = (
    {"mode": "api", "stability": "unknown", "maintenance": "unknown", "compliance": "unassessed", "citation": "unknown", "recommendation": "not_selected_no_official_access_identified"},
    {"mode": "rss", "stability": "unverified", "maintenance": "potentially_low", "compliance": "metadata_only_pending_payload_and_terms_validation", "citation": "potentially_good", "recommendation": "future_discovery_candidate_after_validation"},
    {"mode": "sitemap", "stability": "unverified", "maintenance": "medium", "compliance": "metadata_only", "citation": "indirect", "recommendation": "html_plan_only_not_xml_ingestion"},
    {"mode": "targeted_pages", "stability": "medium", "maintenance": "medium", "compliance": "metadata_only_fail_closed", "citation": "good", "recommendation": "preferred_current_architecture"},
    {"mode": "manual_ingestion", "stability": "high", "maintenance": "high", "compliance": "human_review_required", "citation": "good", "recommendation": "exceptional_fallback"},
)

RECOMMENDATION = {
    "primary": "targeted_pages_metadata_only",
    "candidate_after_validation": "rss_metadata_discovery",
    "fallback": "manual_ingestion_with_legal_review",
    "refresh_frequency": "weekly_manual_review",
    "network_transport_implemented": False,
    "synchronization_enabled": False,
}

SAMPLE = (
    DocumentSample("https://grand-est.dreets.gouv.fr/Travail-et-relations-sociales", "Travail et relations sociales", None, "relations_collectives", "dossier"),
    DocumentSample("https://grand-est.dreets.gouv.fr/Inspection-du-travail", "Inspection du travail", None, "inspection_du_travail", "dossier"),
    DocumentSample("https://grand-est.dreets.gouv.fr/Sante-au-travail", "Santé au travail", "2022-12-09", "sante_au_travail", "fiche"),
    DocumentSample("https://grand-est.dreets.gouv.fr/sites/grand-est.dreets.gouv.fr/IMG/pdf/guide_negociation_cse_juillet_2020.pdf", "Guide négociation CSE", "2020-07", "cse", "guide"),
    DocumentSample("https://grand-est.dreets.gouv.fr/sites/grand-est.dreets.gouv.fr/IMG/pdf/ue57_dialogsocial_docnumerique_a4-interactif.pdf", "Attributions", None, "dialogue_social_moselle", "publication"),
)


def build_review() -> dict[str, object]:
    """Return a serialization-safe study record without performing I/O."""
    return {
        "review_date": REVIEW_DATE,
        "consulted_domains": list(CONSULTED_DOMAINS),
        "logical_request_count": LOGICAL_REQUEST_COUNT,
        "access_study": list(ACCESS_STUDY),
        "evidence": [asdict(item) for item in EVIDENCE],
        "page_structure": dict(PAGE_STRUCTURE),
        "document_policy": dict(DOCUMENT_POLICY),
        "architecture_comparison": list(ARCHITECTURE_COMPARISON),
        "recommendation": dict(RECOMMENDATION),
        "sample": [item.to_dict() for item in SAMPLE],
    }
