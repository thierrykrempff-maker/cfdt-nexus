#!/usr/bin/env python
"""Expert Paie V0 for local Nexus analyses."""

from __future__ import annotations

from typing import Any

from .utils import collect_issue_values, has_any, normalize, route_domains, source_documents, unique


PAIE_KEYWORDS = [
    "paie",
    "bulletin",
    "salaire",
    "coefficient",
    "classification",
    "heures supplementaires",
    "heure supplementaire",
    "heures de nuit",
    "nuit",
    "dimanche",
    "jour ferie",
    "jours feries",
    "astreinte",
    "intervention",
    "prime",
    "majoration",
    "recuperation",
    "repos compensateur",
    "compteur",
    "pointage",
]


def applies(answer: dict[str, Any]) -> bool:
    domains = route_domains(answer)
    query = answer.get("query", "")
    if "paie_remuneration" in domains:
        return True
    if has_any(query, ["bulletin", "paie", "salaire", "majoration", "prime", "compteur", "pointage"]):
        return True
    if has_any(query, ["coefficient", "classification"]) and has_any(query, ["bulletin", "salaire", "paie"]):
        return True
    return False


def is_incomplete_prime_query(answer: dict[str, Any]) -> bool:
    query = normalize(answer.get("query", ""))
    return "prime" in query and not has_any(
        query,
        [
            "nuit",
            "dimanche",
            "jour ferie",
            "astreinte",
            "montant",
            "taux",
            "periode",
            "bulletin",
            "coefficient",
        ],
    )


def object_of_control(answer: dict[str, Any]) -> str:
    query = answer.get("query", "")
    if is_incomplete_prime_query(answer):
        return "Controle d'une prime non identifiee : Nexus doit d'abord connaitre le libelle, la periode et la regle applicable."
    if has_any(query, ["astreinte", "intervention"]):
        return "Controle paie d'une intervention pendant astreinte, avec heures, majorations, recuperation et compteurs."
    if has_any(query, ["nuit", "dimanche", "jour ferie", "majoration"]):
        return "Controle des heures de nuit, dimanche ou jour ferie et des majorations correspondantes sur le bulletin."
    if has_any(query, ["coefficient", "classification", "salaire de base"]):
        return "Controle du salaire de base au regard du coefficient, de la classification et des textes applicables."
    if has_any(query, ["prime"]):
        return "Controle d'une prime ou d'un element variable de remuneration."
    return "Controle paie methodologique a partir du bulletin, du pointage, des compteurs et des sources locales."


def bulletin_elements(answer: dict[str, Any]) -> list[str]:
    query = answer.get("query", "")
    elements: list[str] = []
    if has_any(query, ["salaire de base", "coefficient", "classification"]):
        elements.extend(["salaire de base", "coefficient ou classification affichee", "taux ou appointement mensuel"])
    if has_any(query, ["nuit"]):
        elements.extend(["heures de nuit", "majoration nuit", "base et taux appliques"])
    if has_any(query, ["dimanche"]):
        elements.extend(["heures du dimanche", "majoration dimanche", "base et taux appliques"])
    if has_any(query, ["jour ferie", "jours feries"]):
        elements.extend(["heures de jour ferie", "majoration jour ferie", "repos ou recuperation associee"])
    if has_any(query, ["astreinte", "intervention"]):
        elements.extend(
            [
                "indemnite ou prime d'astreinte",
                "heures d'intervention",
                "majorations eventuelles nuit, dimanche ou jour ferie",
                "recuperation ou repos compensateur",
                "compteurs horaires",
            ]
        )
    if has_any(query, ["prime"]):
        elements.extend(["libelle exact de la prime", "base de calcul", "montant verse", "periode rattachee"])
    if not elements:
        elements.extend(["rubriques du bulletin concernees", "base de calcul", "taux", "montant verse"])
    return unique(elements, limit=10)


def available_rules(answer: dict[str, Any]) -> list[str]:
    sources = source_documents(answer)
    if not sources:
        return ["Aucune source locale principale n'est disponible dans la reponse Nexus."]
    return ["Source locale a verifier: " + source for source in sources]


def data_needed(answer: dict[str, Any]) -> list[str]:
    query = answer.get("query", "")
    values = [
        "periode de paie controlee",
        "bulletin de paie detaille de la periode",
        "pointage ou releve horaire valide",
        "compteurs horaires avant et apres paie",
        "regle locale applicable a la rubrique controlee",
        "taux ou montant applique sur le bulletin",
    ]
    if has_any(query, ["nuit", "dimanche", "jour ferie", "astreinte", "intervention"]):
        values.extend(
            [
                "heure de debut et de fin de chaque sequence",
                "qualification des plages nuit, dimanche ou jour ferie",
                "detail des majorations ou recuperations appliquees",
            ]
        )
    if has_any(query, ["astreinte", "intervention"]):
        values.extend(
            [
                "declenchement de l'astreinte",
                "duree d'intervention retenue",
                "temps annexes retenus ou exclus par la source applicable",
            ]
        )
    if has_any(query, ["prime"]):
        values.extend(["libelle exact de la prime", "condition d'ouverture de la prime", "assiette ou formule de calcul"])
    if has_any(query, ["coefficient", "classification", "salaire de base"]):
        values.extend(["coefficient applicable", "classification retenue", "grille ou texte de remuneration applicable"])
    return unique(values, limit=14)


def control_method(answer: dict[str, Any]) -> list[str]:
    query = answer.get("query", "")
    steps = [
        "Identifier la rubrique controlee, la periode et la source locale applicable.",
        "Rapprocher pointage, planning, compteurs et bulletin sans additionner des elements de nature differente.",
        "Verifier la base, le taux, le nombre d'heures ou le montant retenu sur le bulletin.",
        "Comparer le resultat attendu au bulletin uniquement apres validation des donnees et du texte applicable.",
    ]
    if has_any(query, ["nuit", "dimanche", "jour ferie"]):
        steps.insert(2, "Isoler les heures situees sur les plages nuit, dimanche ou jour ferie avant de chercher la majoration.")
    if has_any(query, ["astreinte", "intervention"]):
        steps.insert(2, "Separarer indemnite d'astreinte, temps d'intervention, majorations et recuperations.")
    if is_incomplete_prime_query(answer):
        steps.insert(0, "Demander d'abord quelle prime est visee et sur quel bulletin elle apparait.")
    return unique(steps, limit=8)


def potential_anomalies(answer: dict[str, Any]) -> list[str]:
    query = answer.get("query", "")
    anomalies = [
        "rubrique absente ou libellee de facon ambigue",
        "nombre d'heures payees different du pointage valide",
        "taux ou base non justifie par la source applicable",
        "ecart entre compteur, bulletin et recapitulatif paie",
    ]
    if has_any(query, ["nuit"]):
        anomalies.append("heures de nuit non isolees ou non majorees selon la source applicable")
    if has_any(query, ["dimanche"]):
        anomalies.append("majoration dimanche absente ou calculee sur une mauvaise base")
    if has_any(query, ["jour ferie"]):
        anomalies.append("traitement jour ferie confondu avec dimanche, nuit ou recuperation")
    if has_any(query, ["astreinte", "intervention"]):
        anomalies.extend(
            [
                "intervention d'astreinte payee sans coherence avec le declenchement et les horaires",
                "recuperation ou repos compensateur absent du compteur",
            ]
        )
    if is_incomplete_prime_query(answer):
        anomalies.append("impossible d'identifier l'anomalie tant que la prime n'est pas nommee")
    return unique(anomalies, limit=10)


def calculation_detail(answer: dict[str, Any]) -> str:
    return (
        "Non produit : Nexus ne dispose pas simultanement des heures validees, du taux ou montant applicable, "
        "de la base de calcul et de la valeur portee au bulletin."
    )


def documents_needed(answer: dict[str, Any]) -> list[str]:
    values = [
        "bulletin de paie de la periode controlee",
        "detail de paie ou recapitulatif des elements variables",
        "pointage ou releve horaire valide",
        "planning de la periode",
        "compteurs horaires et recuperations",
    ]
    values.extend(str(item) for item in answer.get("documents_to_request", []))
    values.extend(collect_issue_values(answer, "documents"))
    return unique(values, limit=12)


def confidence(answer: dict[str, Any]) -> str:
    if is_incomplete_prime_query(answer):
        return "faible"
    if not answer.get("sources"):
        return "faible"
    return "moyen"


def limits(answer: dict[str, Any]) -> list[str]:
    items = [
        "L'expert paie V0 ne calcule pas sans bulletin, pointage, taux applicable et source de calcul.",
        "Il ne lit aucun document externe et n'envoie aucune donnee hors du poste local.",
        "Les sources retrouvees doivent etre relues pour confirmer leur champ d'application.",
    ]
    if is_incomplete_prime_query(answer):
        items.append("La question est trop incomplete pour identifier la rubrique ou la regle de prime.")
    return unique(items, limit=8)


def enrich(answer: dict[str, Any]) -> dict[str, Any]:
    if not applies(answer):
        return {
            "active": False,
            "name": "Expert Paie V0",
            "reason": "Question hors perimetre paie pour cette orchestration.",
        }
    return {
        "active": True,
        "name": "Expert Paie V0",
        "objet_du_controle": object_of_control(answer),
        "elements_du_bulletin_concernes": bulletin_elements(answer),
        "regles_ou_sources_disponibles": available_rules(answer),
        "donnees_necessaires_au_calcul": data_needed(answer),
        "methode_de_controle": control_method(answer),
        "anomalies_potentielles": potential_anomalies(answer),
        "calcul_detaille": calculation_detail(answer),
        "documents_necessaires": documents_needed(answer),
        "sources_utilisees": source_documents(answer),
        "niveau_de_confiance": confidence(answer),
        "limites": limits(answer),
    }
