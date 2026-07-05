#!/usr/bin/env python
"""
CFDT Nexus local bridge:
Document / CSE topic -> Bible Accords Sarralbe.

This script is local-only. It never sends private documents to an external API and
never writes real document content into Git. Generated reports stay under
local-index/agreements/integration/.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import agreements_bible as bible


BRIDGE_DIR = bible.LOCAL_ROOT / "integration"
BRIDGE_REPORT_DIR = BRIDGE_DIR / "reports"
BRIDGE_TEST_DIR = BRIDGE_DIR / "tests"

PRUDENCE_WARNING = (
    "L'analyse automatique constitue une aide à la préparation. Vérifier les textes cités, "
    "leur date, leur champ d'application et leur articulation avec les normes supérieures "
    "avant toute position définitive en CSE, CSSCT ou négociation."
)

SOURCE_FOUND = "SOURCE LOCALE TROUVÉE"
SOURCE_TO_VERIFY = "SOURCE LOCALE À VÉRIFIER"
NO_RELEVANT_SOURCE = "AUCUNE SOURCE LOCALE PERTINENTE TROUVÉE"


THEME_RULES = [
    {
        "theme": "temps de travail / repos / 5x8",
        "patterns": [
            "repos entre postes",
            "repos entre deux postes",
            "repos quotidien",
            "changement de cycle",
            "cycle de travail",
            "modification des horaires",
            "horaires postés",
            "horaires postes",
            "5x8",
            "travail posté",
            "travail poste",
            "travail de nuit",
            "temps de repos",
        ],
        "queries": [
            "repos entre deux postes",
            "temps de travail 5x8 horaires postés",
            "repos quotidien travail posté",
            "travail de nuit organisation du travail",
        ],
        "comparison_points": [
            "disposition actuelle sur l'organisation du travail",
            "proposition nouvelle sur les horaires ou le repos",
            "compatibilité à vérifier avec les textes locaux 5x8 / temps de travail",
            "impact possible sur fatigue, vie familiale et sécurité",
        ],
        "questions": [
            "Quel est le changement concret demandé par rapport à l'organisation actuelle ?",
            "Quels salariés, équipes ou cycles sont concernés ?",
            "Quel délai de prévenance et quelle période de test sont prévus ?",
            "Quel impact sur le repos quotidien, le travail de nuit et la fatigue ?",
        ],
        "documents_to_request": [
            "planning actuel et projeté",
            "note de présentation détaillée",
            "analyse d'impact santé-sécurité",
            "liste des populations concernées",
        ],
    },
    {
        "theme": "astreinte",
        "patterns": [
            "astreinte",
            "intervention",
            "indemnisation des interventions",
            "régime d'astreinte",
            "regime d'astreinte",
        ],
        "queries": [
            "astreinte indemnisation interventions",
            "régime d'astreinte intervention",
            "temps d'intervention astreinte",
        ],
        "comparison_points": [
            "régime actuel d'astreinte",
            "indemnisation proposée ou modifiée",
            "articulation temps d'intervention / temps de repos",
        ],
        "questions": [
            "Quelles catégories de salariés seraient concernées ?",
            "L'indemnisation change-t-elle ?",
            "Comment le repos après intervention est-il garanti ?",
        ],
        "documents_to_request": [
            "projet d'organisation des astreintes",
            "barème d'indemnisation",
            "bilan des interventions passées",
        ],
    },
    {
        "theme": "disciplinaire / règlement intérieur",
        "patterns": [
            "sanction",
            "discipline",
            "disciplinaire",
            "avertissement",
            "mise à pied",
            "mise a pied",
            "entretien disciplinaire",
            "règlement intérieur",
            "reglement interieur",
        ],
        "queries": [
            "règlement intérieur procédure disciplinaire sanction avertissement",
            "entretien disciplinaire avertissement",
            "mise à pied disciplinaire procédure",
        ],
        "comparison_points": [
            "faits reprochés",
            "procédure prévue par le règlement intérieur",
            "sanction envisagée",
            "délais et garanties de défense",
        ],
        "questions": [
            "Quels faits précis sont reprochés et à quelle date ?",
            "Le salarié a-t-il été convoqué et informé de l'objet de l'entretien ?",
            "Quels éléments de preuve existent ?",
        ],
        "documents_to_request": [
            "convocation",
            "éléments reprochés",
            "règlement intérieur applicable",
            "témoignages ou éléments de contexte",
        ],
    },
    {
        "theme": "relations collectives / droit syndical",
        "patterns": [
            "cse",
            "heures de délégation",
            "heures de delegation",
            "crédit d'heures",
            "credit d'heures",
            "moyens syndicaux",
            "droit syndical",
            "mandat",
            "représentant du personnel",
            "representant du personnel",
            "rp",
            "délégué syndical",
            "delegue syndical",
            "représentant syndical",
            "representant syndical",
            "élu cse",
            "elu cse",
        ],
        "queries": [
            "heures de délégation droit syndical",
            "crédit d'heures mandat représentant du personnel",
            "accord CSE moyens syndicaux",
            "représentant syndical délégué syndical",
        ],
        "comparison_points": [
            "moyens actuels des représentants",
            "heures ou crédits d'heures concernés",
            "mandats et populations concernées",
            "articulation avec accord CSE / droit syndical",
        ],
        "questions": [
            "Quels mandats ou représentants sont concernés ?",
            "Le crédit d'heures est-il modifié, déplacé ou conditionné ?",
            "La consultation du CSE ou des organisations syndicales est-elle prévue ?",
        ],
        "documents_to_request": [
            "projet de modification des moyens",
            "accord CSE ou droit syndical applicable",
            "état actuel des crédits d'heures",
        ],
    },
    {
        "theme": "rémunération / primes",
        "patterns": [
            "rémunération",
            "remuneration",
            "salaire",
            "salaires",
            "prime",
            "primes",
            "majoration",
            "dimanche",
            "jour férié",
            "jour ferie",
            "nuit",
            "intéressement",
            "interessement",
            "participation",
        ],
        "queries": [
            "rémunération salaires primes",
            "prime de nuit majoration dimanche jour férié",
            "intéressement participation épargne salariale",
        ],
        "comparison_points": [
            "disposition actuelle sur rémunération ou prime",
            "montant ou condition proposé",
            "population bénéficiaire ou exclue",
        ],
        "questions": [
            "Quel montant ou quelle formule change ?",
            "Quels salariés sont concernés ?",
            "La mesure est-elle pérenne ou temporaire ?",
        ],
        "documents_to_request": [
            "note de calcul",
            "périmètre salariés concernés",
            "texte projeté",
        ],
    },
]


SCENARIOS = [
    {
        "id": "test-1-repos-5x8",
        "kind": "cse",
        "title": "Modification du repos entre deux postes",
        "text": "La direction souhaite modifier le repos entre deux postes pour les salariés en 5x8.",
        "expected": "les textes 5x8 et temps de travail doivent remonter prioritairement",
    },
    {
        "id": "test-2-astreinte",
        "kind": "cse",
        "title": "Modification astreinte",
        "text": "La direction envisage une modification du régime d'astreinte et de l'indemnisation des interventions.",
        "expected": "l'accord Astreinte doit être prioritaire",
    },
    {
        "id": "test-3-discipline",
        "kind": "cse",
        "title": "Procédure disciplinaire",
        "text": "Un salarié fait l'objet d'une procédure disciplinaire pouvant conduire à un avertissement.",
        "expected": "le règlement intérieur doit être prioritaire",
    },
    {
        "id": "test-4-droit-syndical",
        "kind": "cse",
        "title": "Moyens de délégation",
        "text": "Modification des moyens et heures de délégation des représentants du personnel.",
        "expected": "accord CSE et textes RP/droit syndical prioritaires",
    },
    {
        "id": "test-5-prime-nuit-dimanche-ferie",
        "kind": "cse",
        "title": "Prime de nuit, dimanche et jour ferie",
        "text": "La direction souhaite revoir les primes de nuit, dimanche et jour ferie.",
        "expected": "les textes remuneration, primes et majorations doivent remonter prioritairement",
    },
]


REQUIRED_CSE_SECTIONS = [
    "2_textes_locaux_potentiellement_concernes",
    "3_situation_actuelle_a_verifier",
    "4_points_a_comparer_avant_apres",
    "5_consequences_concretes_pour_les_salaries",
    "8_informations_manquantes",
    "10_questions_principales_a_poser_en_cse",
    "11_relances_conditionnelles",
    "14_synthese_pour_l_elu",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def ensure_dirs() -> None:
    bible.ensure_dirs()
    for directory in [BRIDGE_DIR, BRIDGE_REPORT_DIR, BRIDGE_TEST_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def write_private_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize(value: str) -> str:
    return bible.normalize(value)


def detect_themes(text: str) -> list[dict[str, Any]]:
    normalized = normalize(text)
    detected = []
    for rule in THEME_RULES:
        hits = []
        for pattern in rule["patterns"]:
            if normalize(pattern) in normalized:
                hits.append(pattern)
        if hits:
            detected.append(
                {
                    "theme": rule["theme"],
                    "matched_terms": hits,
                    "queries": rule["queries"],
                    "comparison_points": rule["comparison_points"],
                    "questions": rule["questions"],
                    "documents_to_request": rule["documents_to_request"],
                }
            )
    return detected


def generated_queries(text: str, themes: list[dict[str, Any]]) -> list[str]:
    queries = []
    for theme in themes:
        queries.extend(theme["queries"])
    if not queries:
        queries.append(text[:180])
    seen = set()
    deduped = []
    for query in queries:
        key = normalize(query)
        if key not in seen:
            seen.add(key)
            deduped.append(query)
    return deduped


def search_bible(query: str, limit: int) -> list[dict[str, Any]]:
    chunks = bible.read_jsonl(bible.INDEX_DIR / "chunks.private.jsonl")
    query_tokens = bible.tokenize(query)
    if not query_tokens:
        return []

    rows = []
    for chunk in chunks:
        details = bible.score_chunk_details(chunk, query_tokens, query)
        if details["total"] <= 0:
            continue
        rows.append((details["total"], chunk, details))
    rows.sort(key=lambda item: item[0], reverse=True)
    sources = []
    for score, chunk, details in rows[:limit]:
        source = bible.format_source(score, chunk, query_tokens, details)
        source["source_status"] = classify_source(score, source)
        source["confidence_level"] = confidence_level(score)
        sources.append(source)
    return sources


def classify_source(score: float, source: dict[str, Any]) -> str:
    if score >= 50 and source.get("page"):
        return SOURCE_FOUND
    if score > 0:
        return SOURCE_TO_VERIFY
    return NO_RELEVANT_SOURCE


def confidence_level(score: float) -> str:
    if score >= 150:
        return "fort"
    if score >= 70:
        return "moyen"
    return "faible"


def merge_sources(searches: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_chunk = {}
    for search in searches:
        for source in search["sources"]:
            chunk_id = source.get("chunk_id")
            if not chunk_id:
                continue
            existing = by_chunk.get(chunk_id)
            if existing is None or source["match_score"] > existing["match_score"]:
                merged = dict(source)
                merged["matched_query"] = search["query"]
                by_chunk[chunk_id] = merged
    return sorted(by_chunk.values(), key=lambda item: item["match_score"], reverse=True)[:limit]


def main_subject(text: str, themes: list[dict[str, Any]]) -> str:
    return themes[0]["theme"] if themes else "sujet à qualifier"


def inferred_intent(text: str, themes: list[dict[str, Any]]) -> str:
    if not themes:
        return "Le document ou point semble présenter un sujet nécessitant qualification humaine."
    theme_names = ", ".join(theme["theme"] for theme in themes[:3])
    return f"Le document ou point semble présenter ou modifier un sujet lié à : {theme_names}."


def comparison_points(themes: list[dict[str, Any]]) -> list[str]:
    points = []
    for theme in themes:
        points.extend(theme["comparison_points"])
    base = [
        "disposition actuelle",
        "proposition nouvelle",
        "différence détectée",
        "compatibilité à vérifier",
        "articulation à analyser",
        "conséquence possible",
        "bénéficiaire probable du changement",
        "risque salarié",
        "avantage éventuel",
        "point ambigu",
    ]
    return dedupe(points + base)


def questions_for(themes: list[dict[str, Any]]) -> list[str]:
    questions = []
    for theme in themes:
        questions.extend(theme["questions"])
    return dedupe(questions + ["Quelle est la base juridique ou conventionnelle invoquée par la direction ?"])


def documents_to_request(themes: list[dict[str, Any]]) -> list[str]:
    docs = []
    for theme in themes:
        docs.extend(theme["documents_to_request"])
    return dedupe(docs + ["texte projeté", "note d'impact", "calendrier de mise en œuvre"])


def dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        key = normalize(value)
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def build_document_analysis(title: str, text: str, limit: int) -> dict[str, Any]:
    themes = detect_themes(text)
    queries = generated_queries(text, themes)
    searches = [{"query": query, "sources": search_bible(query, limit)} for query in queries]
    sources = merge_sources(searches, limit)
    source_status = sources[0]["source_status"] if sources else NO_RELEVANT_SOURCE
    return {
        "kind": "document-analysis",
        "generated_at": now_iso(),
        "title": title,
        "prudence_warning": PRUDENCE_WARNING,
        "source_status": source_status,
        "A_sujet_principal": main_subject(text, themes),
        "B_ce_que_le_document_semble_vouloir_modifier_ou_presenter": inferred_intent(text, themes),
        "C_textes_locaux_potentiellement_concernes": sources,
        "D_points_de_comparaison": comparison_points(themes),
        "detected_themes": themes,
        "generated_queries": queries,
        "points_to_verify": [
            "Vérifier la date et le champ d'application des textes cités.",
            "Vérifier s'il existe un accord, avenant ou usage plus récent.",
            "Ne pas conclure à une violation juridique sans analyse humaine.",
        ],
        "security_notice": "Private local analysis. Do not commit generated reports.",
    }


def theme_names(themes: list[dict[str, Any]]) -> list[str]:
    return [theme["theme"] for theme in themes]


def has_theme(themes: list[dict[str, Any]], *needles: str) -> bool:
    haystack = normalize(" ".join(theme_names(themes)))
    return any(normalize(needle) in haystack for needle in needles)


def source_reference(source: dict[str, Any]) -> str:
    parts = [source.get("document") or "document local"]
    if source.get("page"):
        parts.append(f"page {source.get('page')}")
    if source.get("article_or_section"):
        parts.append(str(source.get("article_or_section")))
    return " / ".join(parts)


def role_probable(source: dict[str, Any], themes: list[dict[str, Any]], index: int) -> str:
    haystack = normalize(
        " ".join(
            str(source.get(key) or "")
            for key in ["document", "matched_query", "ranking_profile", "article_or_section"]
        )
    )
    main_theme = normalize(theme_names(themes)[0]) if themes else ""
    if "reglement" in haystack or "interieur" in haystack:
        return "règlement intérieur"
    if "convention" in haystack or "ccnic" in haystack:
        return "convention collective"
    if "historique" in haystack or "ancien" in haystack:
        return "document historique"
    if "remuneration" not in main_theme and any(
        term in haystack for term in ["nao", "salaire", "prime", "interessement", "participation"]
    ):
        return "document potentiellement non prioritaire"
    if index == 0 and source.get("source_status") == SOURCE_FOUND:
        return "texte principal"
    if index <= 2 and source.get("source_status") == SOURCE_FOUND:
        return "texte complémentaire"
    return "texte à vérifier"


def enrich_sources_for_cse(sources: list[dict[str, Any]], themes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for index, source in enumerate(sources):
        reasons = source.get("ranking_reasons") or []
        enriched.append(
            {
                "document": source.get("document"),
                "page": source.get("page"),
                "article": source.get("article_or_section"),
                "score": source.get("match_score"),
                "raison_de_pertinence": "; ".join(reasons[:3]) if reasons else "Correspondance locale à vérifier.",
                "role_probable_du_document": role_probable(source, themes, index),
                "statut_source": source.get("source_status"),
                "niveau_de_confiance": source.get("confidence_level"),
                "requete_associee": source.get("matched_query"),
            }
        )
    return enriched


def cse_confidence(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "faible"
    best_score = max(float(source.get("match_score") or 0) for source in sources)
    if best_score >= 150:
        return "fort"
    if best_score >= 70:
        return "moyen"
    return "faible"


def direction_intent(text: str, themes: list[dict[str, Any]]) -> str:
    if not themes:
        return "Le changement exact doit être précisé par la direction."
    if has_theme(themes, "temps de travail", "repos", "5x8"):
        return (
            "La direction semble vouloir modifier l'organisation du repos, des horaires ou du cycle 5x8. "
            "Le changement exact doit être précisé par la direction."
        )
    if has_theme(themes, "astreinte"):
        return (
            "La direction semble vouloir modifier le régime d'astreinte, l'organisation des interventions "
            "ou leur indemnisation. Les modalités exactes doivent être précisées."
        )
    if has_theme(themes, "disciplinaire"):
        return (
            "Le sujet semble porter sur une procédure disciplinaire ou sur l'application du règlement intérieur. "
            "Les faits, délais et garanties de défense doivent être précisés."
        )
    if has_theme(themes, "droit syndical", "relations collectives"):
        return (
            "La direction semble vouloir modifier ou encadrer les moyens des représentants du personnel. "
            "Le périmètre exact des mandats et droits concernés doit être précisé."
        )
    if has_theme(themes, "rémunération", "primes"):
        return (
            "La direction semble vouloir modifier une prime, une majoration ou une modalité de rémunération collective. "
            "Le montant, les bénéficiaires et la durée doivent être précisés."
        )
    return "Le changement exact doit être précisé par la direction."


def current_situation_checks(themes: list[dict[str, Any]], sources: list[dict[str, Any]]) -> list[str]:
    ref = source_reference(sources[0]) if sources else "une source locale à identifier"
    checks = []
    if has_theme(themes, "temps de travail", "repos", "5x8"):
        checks.extend(
            [
                f"À vérifier dans {ref} : règle actuelle de repos et éventuelles dérogations.",
                f"À vérifier dans {ref} : cycle actuel, salariés concernés et délai de prévenance.",
                f"À vérifier dans {ref} : garanties, contreparties et articulation avec le travail de nuit.",
            ]
        )
    if has_theme(themes, "astreinte"):
        checks.extend(
            [
                f"À vérifier dans {ref} : régime actuel d'astreinte et conditions d'intervention.",
                f"À vérifier dans {ref} : indemnisation, repos après intervention et population concernée.",
            ]
        )
    if has_theme(themes, "disciplinaire"):
        checks.extend(
            [
                f"À vérifier dans {ref} : procédure disciplinaire applicable et garanties de défense.",
                f"À vérifier dans {ref} : sanctions prévues, délais et modalités de convocation.",
            ]
        )
    if has_theme(themes, "droit syndical", "relations collectives"):
        checks.extend(
            [
                f"À vérifier dans {ref} : crédits d'heures, mandats concernés et moyens syndicaux existants.",
                f"À vérifier dans {ref} : modalités d'utilisation, suivi et garanties des représentants.",
            ]
        )
    if has_theme(themes, "rémunération", "primes"):
        checks.extend(
            [
                f"À vérifier dans {ref} : prime ou majoration actuelle, bénéficiaires et conditions d'ouverture.",
                f"À vérifier dans {ref} : règles existantes de calcul, périodicité et exclusions éventuelles.",
            ]
        )
    return dedupe(checks or [f"À vérifier dans {ref} : disposition actuelle, champ d'application et texte le plus récent."])


def comparison_elements(themes: list[dict[str, Any]]) -> list[str]:
    if has_theme(themes, "temps de travail", "repos", "5x8"):
        return [
            "durée de repos",
            "délai de prévenance",
            "cycle de travail",
            "salariés concernés",
            "volontariat",
            "contreparties",
            "fatigue",
            "sécurité",
            "articulation avec l'accord 5x8",
            "articulation avec la convention collective",
        ]
    if has_theme(themes, "astreinte"):
        return [
            "périmètre de l'astreinte",
            "fréquence d'appel",
            "temps d'intervention",
            "repos après intervention",
            "indemnisation",
            "volontariat ou rotation",
            "sécurité",
        ]
    if has_theme(themes, "disciplinaire"):
        return [
            "faits reprochés",
            "délai de procédure",
            "convocation",
            "preuve",
            "proportionnalité de la sanction",
            "droits de défense",
        ]
    if has_theme(themes, "droit syndical", "relations collectives"):
        return [
            "mandats concernés",
            "crédit d'heures",
            "modalités d'utilisation",
            "moyens syndicaux",
            "information du CSE",
            "égalité entre représentants",
        ]
    if has_theme(themes, "rémunération", "primes"):
        return [
            "montant actuel",
            "montant projeté",
            "bénéficiaires",
            "conditions d'attribution",
            "période d'application",
            "effet paie",
            "égalité de traitement",
        ]
    return ["salariés concernés", "fréquence d'utilisation", "contreparties", "égalité de traitement"]


def comparison_table(themes: list[dict[str, Any]], sources: list[dict[str, Any]]) -> list[dict[str, str]]:
    refs = [source_reference(source) for source in sources] or ["source locale à identifier"]
    return [
        {
            "element": element,
            "situation_actuelle": f"À vérifier dans {refs[index % len(refs)]}.",
            "projet_direction": "À préciser par la direction dans un tableau avant/après.",
            "ecart_ou_changement": "Écart à objectiver après réception du projet écrit.",
            "risque_ou_effet_possible": "Risque ou effet à qualifier avec les salariés concernés.",
            "source_a_verifier": refs[index % len(refs)],
        }
        for index, element in enumerate(comparison_elements(themes))
    ]


def employee_consequences(themes: list[dict[str, Any]]) -> list[dict[str, str]]:
    cssct_sensitive = has_theme(themes, "temps de travail", "repos", "5x8", "astreinte")
    remuneration_sensitive = has_theme(themes, "rémunération", "primes")
    return [
        {"categorie": "charge de travail", "analyse": "Impact potentiel à mesurer selon la fréquence et les postes concernés."},
        {"categorie": "fatigue", "analyse": "Risque potentiel renforcé si le sujet touche repos, 5x8, astreinte ou travail de nuit." if cssct_sensitive else "À vérifier selon l'organisation concrète."},
        {"categorie": "sommeil", "analyse": "À analyser en CSSCT si travail de nuit, repos réduit ou astreinte sont concernés." if cssct_sensitive else "Impact non établi à ce stade."},
        {"categorie": "vie personnelle", "analyse": "Effet possible sur organisation familiale, prévisibilité et récupération."},
        {"categorie": "santé", "analyse": "À croiser avec prévention, médecine du travail et DUERP si le sujet a un impact organisationnel."},
        {"categorie": "sécurité", "analyse": "Point de vigilance si fatigue, récupération ou erreurs opérationnelles peuvent augmenter."},
        {"categorie": "organisation familiale", "analyse": "À mesurer selon délais de prévenance, fréquence et caractère temporaire ou permanent."},
        {"categorie": "récupération", "analyse": "À vérifier dans les textes locaux et avec les plannings simulés."},
        {"categorie": "égalité de traitement", "analyse": "Comparer populations incluses, exclues et critères d'application."},
        {"categorie": "rémunération éventuelle", "analyse": "Impact direct à chiffrer." if remuneration_sensitive else "À vérifier si une contrepartie financière est proposée."},
        {"categorie": "impact sur postés", "analyse": "Point prioritaire si les salariés en 5x8, équipes postées ou travail de nuit sont concernés."},
        {"categorie": "impact sur astreinte", "analyse": "À vérifier si intervention, rappel ou continuité de production sont dans le projet."},
    ]


def benefit_balance(themes: list[dict[str, Any]]) -> dict[str, Any]:
    employee_benefits = [
        "rémunération éventuelle à chiffrer",
        "organisation plus prévisible si le dispositif est encadré",
        "volontariat si prévu par le projet",
        "garanties écrites",
        "repos compensateur si prévu",
        "autres contreparties à négocier",
    ]
    if has_theme(themes, "rémunération", "primes"):
        employee_benefits.insert(0, "gain financier potentiel à vérifier sur fiche de paie et population concernée")
    return {
        "avantages_probables_pour_l_entreprise": [
            "flexibilité",
            "remplacement plus facile",
            "couverture des postes",
            "continuité de production",
            "optimisation des effectifs",
            "baisse de contraintes organisationnelles",
        ],
        "avantages_eventuels_pour_les_salaries": dedupe(employee_benefits),
        "conclusion": "Équilibre social à vérifier.",
    }


def risk_watchpoints(themes: list[dict[str, Any]]) -> list[str]:
    risks = [
        "risque juridique à qualifier avec une source précise",
        "compatibilité à analyser avec les textes locaux, la convention collective et le Code du travail",
        "risque d'absence de contrepartie",
        "risque d'impact sur un autre accord",
        "risque de perte de droit si le projet modifie une garantie existante",
    ]
    if has_theme(themes, "temps de travail", "repos", "5x8", "astreinte"):
        risks.extend(
            [
                "risque santé-sécurité",
                "risque fatigue",
                "risque RPS",
                "risque de banalisation d'une dérogation",
                "risque sur récupération et sécurité process",
            ]
        )
    if has_theme(themes, "disciplinaire"):
        risks.extend(["risque de procédure insuffisamment documentée", "risque de sanction disproportionnée à vérifier"])
    if has_theme(themes, "rémunération", "primes"):
        risks.extend(["risque d'inégalité de traitement", "risque d'effet paie mal chiffré"])
    return dedupe(risks)


def missing_information(themes: list[dict[str, Any]]) -> list[str]:
    missing = [
        "texte exact du projet",
        "comparaison avant/après",
        "salariés concernés",
        "fréquence prévue",
        "durée de la mesure",
        "justification direction",
        "données chiffrées",
        "contreparties proposées",
    ]
    if has_theme(themes, "temps de travail", "repos", "5x8", "astreinte"):
        missing.extend(["analyse de risques", "avis du médecin du travail si pertinent", "consultation CSSCT si pertinente", "mesures de prévention"])
    return dedupe(missing)


def documents_to_request_detailed(themes: list[dict[str, Any]]) -> list[str]:
    documents = [
        "projet écrit complet",
        "tableau comparatif ancien/nouveau",
        "note explicative direction",
        "analyse d'impact",
        "planning ou simulations",
        "historique des dérogations existantes",
    ]
    if has_theme(themes, "temps de travail", "repos", "5x8", "astreinte"):
        documents.extend(["données d'absentéisme/fatigue si pertinentes", "évaluation des risques", "mise à jour DUERP si pertinente", "avis ou contribution CSSCT si nécessaire"])
    if has_theme(themes, "rémunération", "primes"):
        documents.extend(["simulation paie", "population bénéficiaire", "coût global et critères d'attribution"])
    return dedupe(documents + documents_to_request(themes))


def main_cse_questions(themes: list[dict[str, Any]]) -> list[str]:
    questions = [
        "Quel problème concret justifie cette modification ?",
        "Sur quels indicateurs la direction s'appuie-t-elle ?",
        "Combien de salariés seraient concernés ?",
        "Quelle comparaison avant/après pouvez-vous communiquer ?",
        "Le dispositif serait-il temporaire ou permanent ?",
        "Comment le CSE pourra-t-il suivre les effets réels après mise en œuvre ?",
    ]
    if has_theme(themes, "temps de travail", "repos", "5x8"):
        questions.extend(["Quelle fréquence d'utilisation est envisagée ?", "Quelles conséquences sur la fatigue ont été évaluées ?", "Quelles mesures de prévention sont prévues ?", "Quelles contreparties sont proposées ?"])
    if has_theme(themes, "astreinte"):
        questions.extend(["Quels postes ou services seraient intégrés au dispositif d'astreinte ?", "Comment le repos après intervention serait-il garanti ?", "Quelle indemnisation est prévue pour l'astreinte et les interventions ?"])
    if has_theme(themes, "disciplinaire"):
        questions.extend(["Quels faits précis sont reprochés et à quelles dates ?", "Quels éléments de preuve ont été communiqués au salarié ?", "La sanction envisagée est-elle proportionnée aux faits établis ?"])
    if has_theme(themes, "droit syndical", "relations collectives"):
        questions.extend(["Quels mandats et quels représentants sont concernés ?", "Le crédit d'heures est-il modifié, conditionné ou déplacé ?", "Quelles garanties sont prévues pour préserver l'exercice du mandat ?"])
    if has_theme(themes, "rémunération", "primes"):
        questions.extend(["Quel montant exact est prévu et pour quelle période ?", "Quels salariés seraient inclus ou exclus du dispositif ?", "Quelle simulation de paie permet de mesurer l'effet réel ?"])
    return dedupe(questions)[:10]


def conditional_followups() -> list[dict[str, Any]]:
    return [
        {"si_reponse_direction": "besoin d'organisation", "relances": ["Quel besoin précis ?", "Depuis quand ?", "Sur quels postes ?", "Avec quelles données ?"]},
        {"si_reponse_direction": "pas d'impact", "relances": ["Quelle évaluation permet de l'affirmer ?", "Qui l'a réalisée ?", "Quels indicateurs seront suivis ?"]},
        {"si_reponse_direction": "c'est légal", "relances": ["Quel texte précis invoquez-vous ?", "Comment l'articulez-vous avec l'accord existant ?", "Quelles garanties sont prévues ?"]},
    ]


def cssct_point(themes: list[dict[str, Any]], text: str) -> dict[str, Any]:
    normalized = normalize(text)
    probable = has_theme(themes, "temps de travail", "repos", "5x8", "astreinte") or any(
        term in normalized for term in ["fatigue", "nuit", "securite", "sante", "risque"]
    )
    return {
        "statut": "Point CSSCT probable" if probable else "Point CSSCT à vérifier selon l'impact santé-sécurité",
        "questions_cssct": [
            "Quels impacts sur la fatigue sont identifiés ?",
            "Quels impacts sur le sommeil et la récupération sont anticipés ?",
            "Quels risques d'erreurs opérationnelles ou de sécurité process sont évalués ?",
            "Quels accidents, presque accidents ou signaux faibles sont à examiner ?",
            "Quel lien avec les RPS est envisagé ?",
            "Le DUERP doit-il être mis à jour ?",
            "Quelles mesures de prévention sont prévues ?",
            "Un suivi médical ou une contribution du médecin du travail est-il nécessaire ?",
        ]
        if probable
        else ["Vérifier si le projet a un impact sur santé, sécurité, conditions de travail ou organisation."],
    }


def cfdt_position_to_build(themes: list[dict[str, Any]]) -> dict[str, Any]:
    non_acceptables = [
        "absence de projet écrit",
        "absence de comparaison avant/après",
        "absence d'analyse d'impact pour les salariés",
        "absence de garantie ou de suivi",
    ]
    if has_theme(themes, "temps de travail", "repos", "5x8", "astreinte"):
        non_acceptables.extend(["réduction de repos ou hausse de contrainte sans prévention", "banalisation d'une dérogation"])
    return {
        "points_non_acceptables_sans_garantie": dedupe(non_acceptables),
        "points_negociables": ["périmètre", "durée d'application", "phase de test", "fréquence maximale", "modalités de suivi CSE/CSSCT"],
        "contreparties_possibles": ["repos compensateur", "prime ou majoration si pertinent", "délai de prévenance renforcé", "volontariat encadré si adapté", "clause de revoyure"],
        "conditions_minimales": ["projet écrit complet", "sources locales vérifiées", "impact salariés objectivé", "consultation des salariés concernés", "validation juridique avant position définitive"],
        "consultation_des_salaries": "Recueillir le retour des salariés concernés avant position définitive.",
        "alternative_a_travailler": "Demander à la direction une alternative moins contraignante et mieux encadrée.",
    }


def elected_summary(missing: list[str], documents: list[str]) -> dict[str, Any]:
    priorities = dedupe([documents[0], documents[1], missing[0], "analyse d'impact salariés"])[:3]
    return {
        "avant_de_prendre_position_demander_en_priorite": priorities,
        "conclusion": "Position définitive à construire après analyse des documents, vérification juridique et retour des salariés concernés.",
    }


def build_detailed_cse_report(title: str, text: str, base: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    themes = base["detected_themes"]
    source_status = base["source_status"]
    confidence = cse_confidence(sources)
    enriched_sources = enrich_sources_for_cse(sources, themes)
    current_checks = current_situation_checks(themes, sources)
    compare_rows = comparison_table(themes, sources)
    consequences = employee_consequences(themes)
    benefits = benefit_balance(themes)
    risks = risk_watchpoints(themes)
    missing = missing_information(themes)
    requested_documents = documents_to_request_detailed(themes)
    questions = main_cse_questions(themes)
    relances = conditional_followups()
    cssct = cssct_point(themes, text)
    cfdt_position = cfdt_position_to_build(themes)
    synthesis = elected_summary(missing, requested_documents)
    return {
        "kind": "cse-point-analysis",
        "generated_at": now_iso(),
        "point_cse": title,
        "titre": title,
        "sujet_detecte": main_subject(text, themes),
        "statut_source_locale": source_status,
        "niveau_de_confiance": confidence,
        "prudence_warning": PRUDENCE_WARNING,
        "source_status": source_status,
        "1_ce_que_la_direction_semble_vouloir_faire": direction_intent(text, themes),
        "2_textes_locaux_potentiellement_concernes": enriched_sources,
        "3_situation_actuelle_a_verifier": current_checks,
        "4_points_a_comparer_avant_apres": compare_rows,
        "5_consequences_concretes_pour_les_salaries": consequences,
        "6_a_qui_profite_le_changement": benefits,
        "7_risques_et_points_de_vigilance": risks,
        "8_informations_manquantes": missing,
        "9_documents_a_demander": requested_documents,
        "10_questions_principales_a_poser_en_cse": questions,
        "11_relances_conditionnelles": relances,
        "12_point_cssct_eventuel": cssct,
        "13_position_cfdt_a_construire": cfdt_position,
        "14_synthese_pour_l_elu": synthesis,
        "prudence_juridique": [
            "Ne pas conclure que le projet est légal ou illégal sans source précise.",
            "Distinguer source locale, hypothèse, analyse syndicale, question à poser et action recommandée.",
            "Confronter les sources locales à la convention collective et au Code du travail avant position définitive.",
        ],
        "1_ce_que_la_direction_semble_vouloir_presenter": direction_intent(text, themes),
        "2_ce_que_nous_savons": {
            "sujet": main_subject(text, themes),
            "themes_detectes": theme_names(themes),
            "requêtes_bible": base["generated_queries"],
        },
        "3_ce_que_disent_les_textes_locaux": sources,
        "4_accords_lies": [
            {
                "document": source.get("document"),
                "page": source.get("page"),
                "article": source.get("article_or_section"),
                "pertinence": source.get("match_score"),
                "niveau_de_confiance": source.get("confidence_level"),
            }
            for source in sources
        ],
        "5_questions_a_poser_a_la_direction": questions,
        "6_questions_de_relance_selon_reponse": relances,
        "7_documents_complementaires_a_demander": requested_documents,
        "8_risques_pour_les_salaries": risks,
        "9_opportunites_eventuelles": ["clarifier les règles applicables", "obtenir des garanties écrites", "préparer une position CFDT argumentée"],
        "10_position_cfdt_a_construire": cfdt_position,
        "11_avis_motive_requis": "à vérifier",
        "12_informations_manquantes_avant_de_prendre_position": missing,
        "detected_themes": themes,
        "generated_queries": base["generated_queries"],
        "security_notice": "Private local CSE analysis. Do not commit generated reports.",
    }


def build_cse_analysis(title: str, text: str, limit: int) -> dict[str, Any]:
    base = build_document_analysis(title, text, limit)
    sources = base["C_textes_locaux_potentiellement_concernes"]
    return build_detailed_cse_report(title, text, base, sources)
    return {
        "kind": "cse-point-analysis",
        "generated_at": now_iso(),
        "point_cse": title,
        "prudence_warning": PRUDENCE_WARNING,
        "source_status": base["source_status"],
        "1_ce_que_la_direction_semble_vouloir_presenter": base["B_ce_que_le_document_semble_vouloir_modifier_ou_presenter"],
        "2_ce_que_nous_savons": {
            "sujet": base["A_sujet_principal"],
            "themes_detectes": [theme["theme"] for theme in base["detected_themes"]],
            "requêtes_bible": base["generated_queries"],
        },
        "3_ce_que_disent_les_textes_locaux": sources,
        "4_accords_lies": [
            {
                "document": source.get("document"),
                "page": source.get("page"),
                "article": source.get("article_or_section"),
                "pertinence": source.get("match_score"),
                "niveau_de_confiance": source.get("confidence_level"),
            }
            for source in sources
        ],
        "5_questions_a_poser_a_la_direction": questions_for(base["detected_themes"]),
        "6_questions_de_relance_selon_reponse": [
            "Pouvez-vous préciser la base du changement proposé ?",
            "Pouvez-vous confirmer que les textes locaux cités ont été pris en compte ?",
            "Quels éléments mesurables permettront d'évaluer l'impact pour les salariés ?",
        ],
        "7_documents_complementaires_a_demander": documents_to_request(base["detected_themes"]),
        "8_risques_pour_les_salaries": [
            "risque à qualifier après lecture des textes cités",
            "compatibilité à vérifier avec les accords locaux",
            "impact concret à objectiver avant position définitive",
        ],
        "9_opportunites_eventuelles": [
            "clarifier les règles applicables",
            "obtenir des garanties écrites",
            "préparer une position CFDT argumentée",
        ],
        "10_position_cfdt_a_construire": "Position à construire après vérification humaine des sources et échanges avec les salariés concernés.",
        "11_avis_motive_requis": "à vérifier",
        "12_informations_manquantes_avant_de_prendre_position": documents_to_request(base["detected_themes"]),
        "security_notice": "Private local CSE analysis. Do not commit generated reports.",
    }


def extract_document_text(path: Path) -> str:
    extension = path.suffix.lower()
    if extension == ".pdf":
        pages, _ = bible.extract_pdf(path)
    elif extension == ".docx":
        pages, _ = bible.extract_docx(path)
    elif extension == ".txt":
        pages, _ = bible.extract_txt(path)
    else:
        raise SystemExit("Format non supporté pour l'analyse documentaire V1.")
    return "\n\n".join(page.get("text", "") for page in pages).strip()


def print_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        print(NO_RELEVANT_SOURCE)
        print("Ne jamais interpréter l'absence de résultat comme l'absence de droit.")
        return
    for source in sources[:8]:
        print(
            f"- {source.get('document')} | page {source.get('page')} | "
            f"{source.get('article_or_section') or 'article non détecté'} | "
            f"score {source.get('match_score')} | {source.get('source_status')}"
        )


def print_list(title: str, values: list[Any], limit: int = 8) -> None:
    print(title)
    for value in values[:limit]:
        if isinstance(value, dict):
            label = value.get("categorie") or value.get("element") or value.get("si_reponse_direction") or value.get("document") or "item"
            detail = value.get("analyse") or value.get("risque_ou_effet_possible") or value.get("relances") or value.get("role_probable_du_document") or ""
            if isinstance(detail, list):
                detail = "; ".join(str(item) for item in detail)
            print(f"- {label}: {detail}")
        else:
            print(f"- {value}")


def print_comparison_rows(rows: list[dict[str, str]], limit: int = 6) -> None:
    print("4. POINTS À COMPARER AVANT / APRÈS")
    for row in rows[:limit]:
        print(
            f"- {row['element']} | actuel: {row['situation_actuelle']} | "
            f"projet: {row['projet_direction']} | vigilance: {row['risque_ou_effet_possible']}"
        )


def print_cse_summary(report: dict[str, Any]) -> None:
    print("POINT CSE")
    print(f"Titre: {report['titre']}")
    print(f"Sujet détecté: {report['sujet_detecte']}")
    print(f"Statut source locale: {report['statut_source_locale']}")
    print(f"Niveau de confiance: {report['niveau_de_confiance']}")
    print("")
    print("1. CE QUE LA DIRECTION SEMBLE VOULOIR FAIRE")
    print(report["1_ce_que_la_direction_semble_vouloir_faire"])
    print("")
    print("2. TEXTES LOCAUX POTENTIELLEMENT CONCERNÉS")
    for source in report["2_textes_locaux_potentiellement_concernes"][:6]:
        print(
            f"- {source.get('document')} | page {source.get('page')} | "
            f"{source.get('article') or 'article non détecté'} | score {source.get('score')} | "
            f"{source.get('role_probable_du_document')}"
        )
        print(f"  raison: {source.get('raison_de_pertinence')}")
    print("")
    print_list("3. SITUATION ACTUELLE À VÉRIFIER", report["3_situation_actuelle_a_verifier"])
    print("")
    print_comparison_rows(report["4_points_a_comparer_avant_apres"])
    print("")
    print_list("5. CONSÉQUENCES CONCRÈTES POUR LES SALARIÉS", report["5_consequences_concretes_pour_les_salaries"], 12)
    print("")
    print("6. À QUI PROFITE LE CHANGEMENT ?")
    print_list("Avantages probables pour l'entreprise", report["6_a_qui_profite_le_changement"]["avantages_probables_pour_l_entreprise"], 6)
    print_list("Avantages éventuels pour les salariés", report["6_a_qui_profite_le_changement"]["avantages_eventuels_pour_les_salaries"], 6)
    print(report["6_a_qui_profite_le_changement"]["conclusion"])
    print("")
    print_list("7. RISQUES ET POINTS DE VIGILANCE", report["7_risques_et_points_de_vigilance"])
    print("")
    print_list("8. INFORMATIONS MANQUANTES", report["8_informations_manquantes"])
    print("")
    print_list("9. DOCUMENTS À DEMANDER", report["9_documents_a_demander"])
    print("")
    print_list("10. QUESTIONS PRINCIPALES À POSER EN CSE", report["10_questions_principales_a_poser_en_cse"], 10)
    print("")
    print_list("11. RELANCES CONDITIONNELLES", report["11_relances_conditionnelles"], 3)
    print("")
    print("12. POINT CSSCT ÉVENTUEL")
    print(report["12_point_cssct_eventuel"]["statut"])
    print_list("Questions CSSCT", report["12_point_cssct_eventuel"]["questions_cssct"], 8)
    print("")
    print("13. POSITION CFDT À CONSTRUIRE")
    print_list("Points non acceptables sans garantie", report["13_position_cfdt_a_construire"]["points_non_acceptables_sans_garantie"], 6)
    print_list("Conditions minimales", report["13_position_cfdt_a_construire"]["conditions_minimales"], 5)
    print("")
    print("14. SYNTHÈSE POUR L'ÉLU")
    for index, item in enumerate(report["14_synthese_pour_l_elu"]["avant_de_prendre_position_demander_en_priorite"], start=1):
        print(f"{index}. {item}")
    print(report["14_synthese_pour_l_elu"]["conclusion"])
    print(PRUDENCE_WARNING)
    return
    print(f"POINT CSE: {report['point_cse']}")
    print(f"Statut source: {report['source_status']}")
    print(f"Sujet: {report['2_ce_que_nous_savons']['sujet']}")
    print("Textes locaux liés:")
    print_sources(report["3_ce_que_disent_les_textes_locaux"])
    print("Questions à poser:")
    for question in report["5_questions_a_poser_a_la_direction"][:6]:
        print(f"- {question}")
    print(PRUDENCE_WARNING)


def print_document_summary(report: dict[str, Any]) -> None:
    print(f"DOCUMENT: {report['title']}")
    print(f"Statut source: {report['source_status']}")
    print(f"Sujet principal: {report['A_sujet_principal']}")
    print("Textes locaux potentiellement concernés:")
    print_sources(report["C_textes_locaux_potentiellement_concernes"])
    print(PRUDENCE_WARNING)


def command_analyze_cse(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    report = build_cse_analysis(args.title or args.subject[:80], args.subject, args.limit)
    path = BRIDGE_REPORT_DIR / f"cse-analysis-{stamp()}.private.json"
    write_private_json(path, report)
    print_cse_summary(report)
    return report


def command_analyze_document(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    path = Path(args.path).expanduser()
    if not path.exists() or not path.is_file():
        raise SystemExit("Document local introuvable.")
    text = extract_document_text(path)
    if not text:
        raise SystemExit("Aucun texte exploitable extrait du document local.")
    report = build_document_analysis(args.title or path.name, text, args.limit)
    output = BRIDGE_REPORT_DIR / f"document-analysis-{stamp()}.private.json"
    write_private_json(output, report)
    print_document_summary(report)
    return report


def command_run_scenarios(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    rows = []
    for scenario in SCENARIOS:
        if scenario["kind"] == "cse":
            report = build_cse_analysis(scenario["title"], scenario["text"], args.limit)
            sources = report["3_ce_que_disent_les_textes_locaux"]
        else:
            report = build_document_analysis(scenario["title"], scenario["text"], args.limit)
            sources = report["C_textes_locaux_potentiellement_concernes"]
        missing_sections = [section for section in REQUIRED_CSE_SECTIONS if not report.get(section)]
        section_check_ok = not missing_sections and bool(sources)
        rows.append(
            {
                "id": scenario["id"],
                "expected": scenario["expected"],
                "source_status": report["source_status"],
                "section_check_ok": section_check_ok,
                "missing_sections": missing_sections,
                "questions_count": len(report.get("10_questions_principales_a_poser_en_cse", [])),
                "comparison_rows_count": len(report.get("4_points_a_comparer_avant_apres", [])),
                "top_sources": [
                    {
                        "document": source.get("document"),
                        "page": source.get("page"),
                        "score": source.get("match_score"),
                        "confidence": source.get("confidence_level"),
                    }
                    for source in sources[:3]
                ],
            }
        )
    report = {
        "generated_at": now_iso(),
        "scenarios": rows,
        "prudence_warning": PRUDENCE_WARNING,
        "security_notice": "Private scenario report. Do not commit.",
    }
    write_private_json(BRIDGE_TEST_DIR / f"integration-scenarios-{stamp()}.private.json", report)
    print("SCÉNARIOS D'INTÉGRATION")
    for row in rows:
        status = "fiche OK" if row["section_check_ok"] else f"fiche incomplète: {', '.join(row['missing_sections'])}"
        print(f"- {row['id']} | {row['source_status']} | {status} | top sources: {len(row['top_sources'])}")
    return report


def command_diagnose(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    chunks = bible.read_jsonl(bible.INDEX_DIR / "chunks.private.jsonl")
    report = {
        "generated_at": now_iso(),
        "bible_index_available": bool(chunks),
        "chunks": len(chunks),
        "commands": [
            "python automation/scripts/nexus_bible_bridge.py analyze-cse --subject \"...\"",
            "python automation/scripts/nexus_bible_bridge.py analyze-document --path \"C:\\\\chemin\\\\document.pdf\"",
            "python automation/scripts/nexus_bible_bridge.py run-scenarios",
        ],
        "prudence_warning": PRUDENCE_WARNING,
        "security_notice": "Local integration diagnostic. Do not commit generated reports.",
    }
    write_private_json(BRIDGE_REPORT_DIR / f"integration-diagnose-{stamp()}.private.json", report)
    print(f"Bible Accords disponible: {'oui' if chunks else 'non'}")
    print(f"Chunks indexés: {len(chunks)}")
    print(PRUDENCE_WARNING)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CFDT Nexus - Bible Accords integration bridge")
    sub = parser.add_subparsers(dest="command", required=True)

    p_cse = sub.add_parser("analyze-cse")
    p_cse.add_argument("--subject", required=True)
    p_cse.add_argument("--title")
    p_cse.add_argument("--limit", type=int, default=6)
    p_cse.add_argument("--format", choices=["detailed"], default="detailed")

    p_doc = sub.add_parser("analyze-document")
    p_doc.add_argument("--path", required=True)
    p_doc.add_argument("--title")
    p_doc.add_argument("--limit", type=int, default=6)

    p_scenarios = sub.add_parser("run-scenarios")
    p_scenarios.add_argument("--limit", type=int, default=5)

    sub.add_parser("diagnose")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "analyze-cse":
        command_analyze_cse(args)
    elif args.command == "analyze-document":
        command_analyze_document(args)
    elif args.command == "run-scenarios":
        command_run_scenarios(args)
    elif args.command == "diagnose":
        command_diagnose(args)
    else:
        raise SystemExit(f"Commande inconnue: {args.command}")


if __name__ == "__main__":
    main()
