"""Versioned, explicit and ordered ANACT URL classification rules."""
from .anact_catalog import FAMILY_BY_ID
from .anact_classification_models import ClassificationRule, UrlCategory
from .anact_models import AnactResourceType, ConfidenceLevel


RULESET_VERSION = "anact-url-rules-v1"

_CATEGORY_BY_RESOURCE_TYPE = {
    AnactResourceType.THEMATIC_PAGE: UrlCategory.THEMATIC_PAGE,
    AnactResourceType.PUBLICATION: UrlCategory.PUBLICATION,
    AnactResourceType.GUIDE: UrlCategory.GUIDE,
    AnactResourceType.TOOL: UrlCategory.TOOL,
    AnactResourceType.STUDY: UrlCategory.STUDY,
    AnactResourceType.DOSSIER: UrlCategory.DOSSIER,
    AnactResourceType.PRACTICAL_SHEET: UrlCategory.PRACTICAL_SHEET,
    AnactResourceType.NEWS: UrlCategory.NEWS,
    AnactResourceType.EVENT: UrlCategory.EVENT,
}


def _catalog_category(family_id: str) -> UrlCategory:
    return _CATEGORY_BY_RESOURCE_TYPE[FAMILY_BY_ID[family_id].resource_type]

CLASSIFICATION_RULES = (
    ClassificationRule(
        "legal_exact",
        RULESET_VERSION,
        10,
        UrlCategory.LEGAL_PAGE,
        ConfidenceLevel.VERY_HIGH,
        "Chemin légal explicitement répertorié.",
        exact_paths=(
            "/mentions-legales",
            "/politique-generale-de-protection-des-donnees-caractere-personnel",
            "/accessibilite",
        ),
    ),
    ClassificationRule(
        "thematic_path",
        RULESET_VERSION,
        20,
        _catalog_category("thematic_pages"),
        ConfidenceLevel.VERY_HIGH,
        "Chemin thématique explicite du catalogue ANACT.",
        exact_paths=("/themes",),
        path_prefixes=("/themes",),
    ),
    ClassificationRule(
        "guide_path",
        RULESET_VERSION,
        20,
        _catalog_category("guides"),
        ConfidenceLevel.HIGH,
        "Chemin de guide explicitement délimité.",
        path_prefixes=("/guides", "/ressources/guides"),
    ),
    ClassificationRule(
        "tool_path",
        RULESET_VERSION,
        20,
        _catalog_category("tools"),
        ConfidenceLevel.HIGH,
        "Chemin d'outil explicitement délimité.",
        path_prefixes=("/outils", "/autodiagnostics", "/ressources/outils"),
    ),
    ClassificationRule(
        "study_path",
        RULESET_VERSION,
        20,
        _catalog_category("studies"),
        ConfidenceLevel.HIGH,
        "Chemin d'étude explicitement délimité.",
        path_prefixes=("/etudes", "/ressources/etudes"),
    ),
    ClassificationRule(
        "dossier_path",
        RULESET_VERSION,
        20,
        _catalog_category("dossiers"),
        ConfidenceLevel.HIGH,
        "Chemin de dossier explicitement délimité.",
        path_prefixes=("/dossiers", "/ressources/dossiers"),
    ),
    ClassificationRule(
        "practical_sheet_path",
        RULESET_VERSION,
        20,
        _catalog_category("practical_sheets"),
        ConfidenceLevel.HIGH,
        "Chemin de fiche pratique explicitement délimité.",
        path_prefixes=("/fiches-pratiques", "/fiche-pratique", "/ressources/fiches-pratiques"),
    ),
    ClassificationRule(
        "publication_path",
        RULESET_VERSION,
        20,
        _catalog_category("publications"),
        ConfidenceLevel.HIGH,
        "Chemin de publication explicitement délimité.",
        path_prefixes=("/publications", "/ressources/publications"),
    ),
    ClassificationRule(
        "news_path",
        RULESET_VERSION,
        20,
        _catalog_category("news"),
        ConfidenceLevel.HIGH,
        "Chemin d'actualité explicitement délimité.",
        path_prefixes=("/actualites", "/actualite"),
    ),
    ClassificationRule(
        "event_path",
        RULESET_VERSION,
        20,
        _catalog_category("events"),
        ConfidenceLevel.HIGH,
        "Chemin d'événement explicitement délimité.",
        path_prefixes=("/evenements", "/evenement"),
    ),
    ClassificationRule(
        "institutional_exact",
        RULESET_VERSION,
        30,
        UrlCategory.INSTITUTIONAL_PAGE,
        ConfidenceLevel.VERY_HIGH,
        "Page institutionnelle explicitement répertoriée.",
        exact_paths=("/", "/qui-sommes-nous", "/missions", "/regions"),
    ),
    ClassificationRule(
        "probable_guide_slug",
        RULESET_VERSION,
        80,
        _catalog_category("guides"),
        ConfidenceLevel.MEDIUM,
        "Le slug contient un marqueur de guide sans chemin de famille certain.",
        slug_tokens=("guide",),
    ),
    ClassificationRule(
        "probable_tool_slug",
        RULESET_VERSION,
        80,
        _catalog_category("tools"),
        ConfidenceLevel.MEDIUM,
        "Le slug contient un marqueur d'outil sans chemin de famille certain.",
        slug_tokens=("outil", "autodiagnostic"),
    ),
    ClassificationRule(
        "probable_study_slug",
        RULESET_VERSION,
        80,
        _catalog_category("studies"),
        ConfidenceLevel.MEDIUM,
        "Le slug contient un marqueur d'étude sans chemin de famille certain.",
        slug_tokens=("etude",),
    ),
)
