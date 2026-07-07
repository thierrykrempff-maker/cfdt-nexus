#!/usr/bin/env python
"""
Expert Juriste droit du travail V0.

The expert enriches a validated Assistant DS Router answer without changing the
route. It only reasons from the router output and the sources already selected.
"""

from __future__ import annotations

from typing import Any


JURISTE_DOMAINS = {
    "cse",
    "droit_syndical",
    "temps_travail",
    "astreinte",
    "classification_carriere",
}

JURISTE_KEYWORDS = [
    "cse",
    "mandat",
    "droit syndical",
    "reunion",
    "delegation",
    "temps de travail",
    "repos",
    "astreinte",
    "classification",
    "coefficient",
    "convention collective",
    "accord",
]


def normalize(value: Any) -> str:
    return str(value or "").casefold()


def applies(answer: dict[str, Any]) -> bool:
    route = answer.get("route", {})
    domains = set(route.get("domains", []))
    query = normalize(answer.get("query", ""))
    if domains & JURISTE_DOMAINS:
        return True
    return any(keyword in query for keyword in JURISTE_KEYWORDS)


def source_label(source: dict[str, Any]) -> str:
    parts = [str(source.get("document") or "Document local")]
    if source.get("page"):
        parts.append(f"page {source['page']}")
    if source.get("article"):
        parts.append(str(source["article"]))
    return " | ".join(parts)


def source_documents(answer: dict[str, Any]) -> list[str]:
    return [source_label(source) for source in answer.get("sources", [])]


def short_response(answer: dict[str, Any]) -> str:
    route = answer.get("route", {})
    domains = set(route.get("domains", []))
    query = normalize(answer.get("query", ""))
    router_short = answer.get("short_answer")
    if "droit_syndical" in domains and "reunion" in query and "repos" in query:
        return (
            "La question releve d'abord du droit syndical et de l'exercice du mandat, avec un point de temps de travail. "
            "Nexus ne conclut pas automatiquement : il faut verifier la qualite du participant, la nature de la reunion CSE "
            "et le texte qui traite le temps de reunion lorsqu'il tombe sur un repos."
        )
    if {"temps_travail", "astreinte", "paie_remuneration"}.issubset(domains):
        return (
            "La situation doit etre separee en trois blocs : repos apres intervention, regime d'astreinte et trace paie. "
            "Nexus ne fixe pas le droit exact sans lire l'accord d'astreinte, les horaires reels et les bulletins."
        )
    if "classification_carriere" in domains:
        return (
            "La classification ne peut pas etre tranchee sur un mot-cle seul. Il faut comparer coefficient, emploi et fonctions "
            "reelles avec les sources classification/carriere trouvees."
        )
    return router_short or "L'expert juriste ne conclut pas sans source locale suffisante."


def certain_points(answer: dict[str, Any]) -> list[str]:
    route = answer.get("route", {})
    domains = [domain for domain in route.get("domains", []) if domain != "bible_accords"]
    points = []
    if domains:
        points.append("Le routage Nexus qualifie la demande sur : " + ", ".join(domains) + ".")
    if answer.get("sources"):
        points.append("Des sources locales ont ete identifiees, mais elles doivent etre relues avant toute position definitive.")
    else:
        points.append("Aucune source locale principale n'est disponible dans la reponse Nexus.")
    if answer.get("issue_groups"):
        points.append("Les enjeux sont separes en groupes : " + ", ".join(group.get("name", group.get("id", "")) for group in answer["issue_groups"]) + ".")
    return points


def depends_on_local_texts(answer: dict[str, Any]) -> list[str]:
    route = answer.get("route", {})
    domains = set(route.get("domains", []))
    query = normalize(answer.get("query", ""))
    items = [
        "la date, le champ d'application et l'eventuel remplacement des textes cites",
        "l'articulation entre accord local, convention collective et normes superieures",
    ]
    if "droit_syndical" in domains or "reunion" in query:
        items.extend(
            [
                "le statut exact du participant a la reunion CSE",
                "la regle applicable au temps de reunion, de delegation ou de representation",
                "le traitement prevu lorsque la reunion tombe sur un repos",
            ]
        )
    if "astreinte" in domains:
        items.extend(
            [
                "le regime d'astreinte applicable a l'intervention",
                "la regle locale sur le repos apres intervention",
            ]
        )
    if "paie_remuneration" in domains:
        items.append("la regle locale de paie ou de majoration effectivement applicable")
    if "classification_carriere" in domains:
        items.extend(["les criteres conventionnels de classification", "les fonctions reellement exercees et leur niveau de responsabilite"])
    return items


def legal_reasoning(answer: dict[str, Any]) -> list[str]:
    route = answer.get("route", {})
    domains = set(route.get("domains", []))
    query = normalize(answer.get("query", ""))
    if "droit_syndical" in domains and "reunion" in query:
        return [
            "Ne pas raisonner comme un projet de modification du repos : la premiere question est celle de l'exercice du mandat ou de la participation CSE.",
            "Qualifier ensuite le temps concerne : temps de reunion, delegation, convocation employeur, invitation ou autre situation.",
            "Seulement apres cette qualification, verifier si le repos 5x8 est affecte et comment le temps doit etre paye, recupere, impute ou neutralise.",
        ]
    if {"temps_travail", "astreinte", "paie_remuneration"}.issubset(domains):
        return [
            "Verifier d'abord si l'intervention releve bien de l'astreinte et quelle duree doit etre retenue.",
            "Traiter separement la question du repos apres intervention et celle de la trace paie.",
            "Ne pas deduire de majoration ou de compensation sans texte local et sans rapprochement avec les bulletins.",
        ]
    if "classification_carriere" in domains:
        return [
            "Identifier le coefficient et l'emploi retenus.",
            "Comparer avec les fonctions reellement exercees, l'autonomie, la technicite et les responsabilites.",
            "Ne demander un reexamen motive qu'apres avoir relie les faits aux criteres conventionnels trouves.",
        ]
    return ["Raisonner en deux temps : source locale applicable, puis faits exacts du dossier."]


def direction_questions(answer: dict[str, Any]) -> list[str]:
    route = answer.get("route", {})
    domains = set(route.get("domains", []))
    query = normalize(answer.get("query", ""))
    questions: list[str] = []
    if "droit_syndical" in domains and "reunion" in query:
        questions.extend(
            [
                "A quel titre le salarie participe-t-il a la reunion CSE ?",
                "Quelle base locale ou conventionnelle fixe le traitement du temps de reunion ?",
                "Comment ce temps est-il trace si la reunion tombe sur un repos 5x8 ?",
            ]
        )
    if "astreinte" in domains:
        questions.extend(
            [
                "Quelle disposition de l'accord d'astreinte est appliquee a cette intervention ?",
                "Quelle heure de fin d'intervention et quelle heure de reprise sont retenues ?",
            ]
        )
    if "paie_remuneration" in domains:
        questions.append("Ou apparait l'intervention sur le bulletin, le compteur ou le recapitulatif paie ?")
    if "classification_carriere" in domains:
        questions.extend(
            [
                "Quels criteres conventionnels justifient le coefficient actuel ?",
                "Quelles fonctions reelles sont reconnues au-dela de la fiche de poste ?",
            ]
        )
    questions.extend(answer.get("questions_to_ask", [])[:3])
    seen = set()
    result = []
    for question in questions:
        key = normalize(question)
        if key and key not in seen:
            seen.add(key)
            result.append(question)
    return result[:8]


def limits(answer: dict[str, Any]) -> list[str]:
    items = [
        "L'expert juriste V0 ne consulte aucune source externe et ne remplace pas une validation juridique humaine.",
        "Il ne dispose que des sources principales selectionnees par le routeur V1.2.",
    ]
    if "Module paie dedie non connecte" in " ".join(answer.get("warnings", [])):
        items.append("Le module paie dedie n'est pas connecte : le controle paie reste methodologique.")
    if not answer.get("sources"):
        items.append("Aucune source locale principale n'a ete trouvee pour conclure.")
    return items


def enrich(answer: dict[str, Any]) -> dict[str, Any]:
    active = applies(answer)
    if not active:
        return {
            "active": False,
            "name": "Expert Juriste droit du travail V0",
            "reason": "Question hors perimetre juriste V0.",
        }
    return {
        "active": True,
        "name": "Expert Juriste droit du travail V0",
        "response_courte": short_response(answer),
        "ce_qui_est_certain": certain_points(answer),
        "ce_qui_depend_des_textes_locaux": depends_on_local_texts(answer),
        "sources_a_verifier": source_documents(answer),
        "raisonnement_juridique_prudent": legal_reasoning(answer),
        "questions_a_poser_direction": direction_questions(answer),
        "niveau_de_confiance": answer.get("confidence", "a verifier"),
        "limites": limits(answer),
    }
