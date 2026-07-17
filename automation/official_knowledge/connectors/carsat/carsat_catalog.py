"""Offline CARSAT architecture catalogue; every access requires later review."""
from .carsat_models import AccessPossibility,CarsatDocumentCategory,CarsatDocumentFamily,CarsatFunctionalDomain,CarsatMission

MISSIONS=tuple(CarsatMission)
DOCUMENT_FAMILIES=tuple(CarsatDocumentFamily)
FUNCTIONAL_DOMAINS=tuple(CarsatFunctionalDomain)
DOCUMENT_CATEGORIES=tuple(CarsatDocumentCategory)

ACCESS_POSSIBILITIES=(
 AccessPossibility("api",notes="existence, scope, terms and stability remain to be verified"),
 AccessPossibility("rss",notes="existence and technical contract remain to be verified"),
 AccessPossibility("html",notes="page structure, canonical metadata and reuse terms remain to be verified"),
 AccessPossibility("pdf",notes="metadata and document-specific rights remain to be verified; no download authorized"),
 AccessPossibility("open_data",notes="catalogues, licences and identifiers remain to be verified"),
 AccessPossibility("manual",notes="manual metadata entry is not implemented in LOT 0"),
)

REFERENCE_POLICY="No stable CARSAT reference scheme is asserted before an official review."
LICENSE_POLICY="Document-specific rights; metadata only pending official legal review."
CITATION_POLICY="Preserve URL, title, CARSAT attribution, date, version, authority, licence and confidence."
PROVENANCE_POLICY="Preserve source identifier, canonical URL and deterministic metadata fingerprint."
