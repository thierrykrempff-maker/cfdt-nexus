"""Inactive source catalogue for the future France Chimie connector."""

from .france_chimie_models import FranceChimieAccessCandidate, FranceChimieAccessStatus


# These names are candidates for a later official review, not an active allowlist.
FRANCE_CHIMIE_DOMAIN_CANDIDATES = ("francechimie.fr", "www.francechimie.fr")
FRANCE_CHIMIE_ACTIVE_DOMAINS: frozenset[str] = frozenset()
FRANCE_CHIMIE_DOMAIN_STATUS = "pending_official_validation"

FRANCE_CHIMIE_ACCESS_CANDIDATES = (
    FranceChimieAccessCandidate("manual_metadata", FranceChimieAccessStatus.NOT_ACTIVATED),
    FranceChimieAccessCandidate("official_html", FranceChimieAccessStatus.PENDING_OFFICIAL_REVIEW),
    FranceChimieAccessCandidate("official_feed", FranceChimieAccessStatus.PENDING_OFFICIAL_REVIEW),
    FranceChimieAccessCandidate("official_api", FranceChimieAccessStatus.PENDING_OFFICIAL_REVIEW),
)

FRANCE_CHIMIE_LICENSE_POLICY = "DOCUMENT_SPECIFIC_PENDING_OFFICIAL_REVIEW"
FRANCE_CHIMIE_PROVENANCE_POLICY = "Canonical URL, publisher and metadata fingerprint are mandatory."
FRANCE_CHIMIE_CITATION_POLICY = "Canonical URL, title and France Chimie attribution are mandatory."
