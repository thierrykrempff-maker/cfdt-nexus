#!/usr/bin/env python
"""
Expert Juriste droit du travail V0 renforce.

The expert enriches a validated Assistant DS Router answer without changing the
route. It only reasons from the router output and the sources already selected.
"""

from __future__ import annotations

from typing import Any

from .utils import has_any, normalize, route_domains, source_documents, unique


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
    "contester",
    "droits",
]

PURE_PAY_CONTROL_KEYWORDS = [
    "bulletin",
    "paie",
    "majoration",
    "salaire",
    "prime",
    "heures de nuit",
    "dimanche",
]

LEGAL_SIGNAL_KEYWORDS = [
    "cse",
    "mandat",
    "delegation",
    "repos",
    "astreinte",
    "classification",
    "fiche de poste",
    "contester",
    "droit",
    "droits",
    "peut-il",
    "peut il",
    "accord",
    "convention collective",
]


def is_pure_pay_control(answer: dict[str, Any]) -> bool:
    query = normalize(answer.get("query", ""))
    domains = route_domains(answer)
    if "paie_remuneration" not in domains and not has_any(query, PURE_PAY_CONTROL_KEYWORDS):
        return False
    if has_any(query, LEGAL_SIGNAL_KEYWORDS):
        return False
    return has_any(query, ["controler", "controle", "manque", "fausse", "bulletin", "majoration", "paie"])


def applies(answer: dict[str, Any]) -> bool:
    domains = route_domains(answer)
    query = answer.get("query", "")
    if is_pure_pay_control(answer):
        return False
    if domains & JURISTE_DOMAINS:
        return True
    return has_any(query, JURISTE_KEYWORDS)


def short_response(answer: dict[str, Any]) -> str:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    router_short = answer.get("short_answer")
    if "droit_syndical" in domains and "reunion" in query and "repos" in query:
        return (
            "La question releve d'abord du mandat CSE et de la qualification du temps de reunion. "
            "Nexus ne conclut pas sans verifier le statut du participant, la nature de la reunion et le texte local "
            "applicable lorsque la reunion tombe sur un repos."
        )
    if {"temps_travail", "astreinte", "paie_remuneration"}.issubset(domains):
        return (
            "La situation doit etre separee entre astreinte, temps d'intervention, repos apres intervention et trace paie. "
            "Le droit exact depend de l'accord d'astreinte, des horaires reels et des bulletins."
        )
    if "classification_carriere" in domains:
        return (
            "Une contestation de classification se prepare en comparant les fonctions reellement exercees, le coefficient "
            "actuel et les criteres des textes applicables. Nexus ne tranche pas sans ces pieces."
        )
    return router_short or "L'expert juriste ne conclut pas sans source locale suffisante."


def qualification(answer: dict[str, Any]) -> str:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    if "droit_syndical" in domains and "reunion" in query:
        return "Situation d'exercice d'un mandat ou de participation CSE, avec incidence possible sur le temps de travail ou le repos."
    if {"temps_travail", "astreinte"}.issubset(domains):
        return "Situation individuelle d'astreinte avec intervention, effet possible sur le repos et reprise du poste."
    if "classification_carriere" in domains:
        return "Situation individuelle de classification/carriere a qualifier au regard des fonctions reellement exercees."
    if "temps_travail" in domains:
        return "Situation de temps de travail ou de repos a rapprocher des textes locaux applicables."
    return "Question juridique locale a qualifier a partir des sources disponibles et des faits exacts."


def established_points(answer: dict[str, Any]) -> list[str]:
    domains = [domain for domain in answer.get("route", {}).get("domains", []) if domain != "bible_accords"]
    points: list[str] = []
    if domains:
        points.append("Regle certaine: le routage Nexus qualifie la demande sur " + ", ".join(domains) + ".")
    if answer.get("sources"):
        points.append("Regle certaine: des sources locales principales ont ete retrouvees et doivent encadrer l'analyse.")
        points.extend("Source locale identifiee: " + source for source in source_documents(answer, limit=4))
    else:
        points.append("Information manquante: aucune source locale principale n'est disponible dans la reponse Nexus.")
    if answer.get("issue_groups"):
        group_names = [str(group.get("name") or group.get("id")) for group in answer["issue_groups"]]
        points.append("Regle certaine: Nexus separe les enjeux en groupes distincts: " + ", ".join(group_names) + ".")
    return points


def depends_on_local_texts(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    items = [
        "Information manquante: date, champ d'application et remplacement eventuel des textes cites.",
        "Information manquante: articulation entre accord local, convention collective et norme superieure applicable.",
    ]
    if "droit_syndical" in domains or "reunion" in query:
        items.extend(
            [
                "Information manquante: statut exact du participant a la reunion CSE.",
                "Information manquante: nature de la reunion et base de convocation ou de participation.",
                "Information manquante: traitement local du temps de reunion, delegation ou representation pendant un repos.",
            ]
        )
    if "astreinte" in domains:
        items.extend(
            [
                "Information manquante: disposition precise de l'accord d'astreinte applicable a l'intervention.",
                "Information manquante: heures reelles de debut, de fin et de reprise du poste.",
            ]
        )
    if "paie_remuneration" in domains:
        items.append("Information manquante: regle locale de paie ou de majoration effectivement appliquee.")
    if "classification_carriere" in domains:
        items.extend(
            [
                "Information manquante: coefficient, emploi repere et fiche de poste actuellement retenus.",
                "Information manquante: fonctions reellement exercees, niveau d'autonomie, technicite et responsabilites.",
            ]
        )
    return unique(items, limit=10)


def legal_reasoning(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    if "droit_syndical" in domains and "reunion" in query:
        return [
            "Regle certaine: la question doit etre qualifiee comme exercice d'un mandat ou participation CSE avant d'etre traitee comme sujet de repos.",
            "Interpretation: le traitement du temps depend de la nature de la reunion et du role exact du salarie.",
            "Hypothese: si la participation est liee au mandat, le temps ne se traite pas comme une simple initiative personnelle.",
            "Information manquante: texte local ou conventionnel fixant le traitement lorsque la reunion tombe sur un repos 5x8.",
        ]
    if {"temps_travail", "astreinte"}.issubset(domains):
        return [
            "Regle certaine: l'intervention d'astreinte, le repos et la paie doivent etre controles separement.",
            "Interpretation: la reprise apres intervention ne peut etre appreciee qu'avec les heures reelles de fin et de reprise.",
            "Hypothese: les temps annexes ne sont a retenir que si la source applicable les integre.",
            "Information manquante: accord d'astreinte applicable, pointage, compteur et bulletin de la periode.",
        ]
    if "classification_carriere" in domains:
        return [
            "Regle certaine: une demande de classification suppose une comparaison entre classement actuel et fonctions reelles.",
            "Interpretation: l'ecart doit etre rattache a des criteres objectifs du texte applicable, pas seulement a un ressenti.",
            "Hypothese: des fonctions depassant durablement la fiche de poste peuvent justifier une demande de reexamen motivee.",
            "Information manquante: criteres conventionnels, coefficient actuel et preuves des missions exercees.",
        ]
    return [
        "Regle certaine: Nexus ne peut raisonner que sur les sources locales retrouvees.",
        "Information manquante: faits exacts et texte applicable a la situation.",
    ]


def vigilance_points(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    points: list[str] = []
    if "droit_syndical" in domains and "reunion" in query:
        points.extend(
            [
                "Risque: assimiler la question a une modification collective du repos alors qu'elle porte d'abord sur le mandat.",
                "Risque: confondre reunion CSE, delegation, invitation et presence volontaire.",
            ]
        )
    if "astreinte" in domains:
        points.extend(
            [
                "Risque: melanger droit au repos, indemnisation d'astreinte et paiement de l'intervention.",
                "Risque: oublier les heures exactes ou les compteurs dans l'analyse de reprise du poste.",
            ]
        )
    if "classification_carriere" in domains:
        points.extend(
            [
                "Risque: demander un reclassement sans relier les faits aux criteres de classification.",
                "Risque: s'appuyer sur une fiche de poste non actualisee sans preuves des fonctions reelles.",
            ]
        )
    if not points:
        points.append("Risque: conclure trop vite sans verifier le champ des sources locales.")
    return points


def proposed_position(answer: dict[str, Any]) -> str:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    if "droit_syndical" in domains and "reunion" in query:
        return (
            "Position de travail: demander la qualification de la reunion, le statut du salarie et le texte de traitement "
            "du temps avant toute conclusion sur paiement, recuperation ou imputation."
        )
    if {"temps_travail", "astreinte"}.issubset(domains):
        return (
            "Position de travail: verifier d'abord l'accord d'astreinte et les horaires reels, puis traiter separement repos, "
            "temps d'intervention et consequences paie."
        )
    if "classification_carriere" in domains:
        return (
            "Position de travail: objectiver l'ecart entre fonctions reelles et classification actuelle, puis demander un "
            "reexamen motive si les criteres du texte applicable sont remplis."
        )
    return answer.get("working_position") or "Position de travail: completer les sources et les faits avant conclusion."


def direction_questions(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
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
                "Quels elements prouvent la duree et la regularite des fonctions exercees ?",
            ]
        )
    questions.extend(answer.get("questions_to_ask", [])[:3])
    return unique(questions, limit=8)


def limits(answer: dict[str, Any]) -> list[str]:
    items = [
        "L'expert juriste ne remplace pas une validation juridique humaine.",
        "Il ne dispose que des sources principales selectionnees par le routeur V1.2, dont Legifrance seulement si le connecteur est configure et a repondu.",
    ]
    if not answer.get("sources"):
        items.append("Aucune source locale principale n'a ete trouvee pour conclure.")
    if answer.get("warnings"):
        items.extend(str(warning) for warning in answer["warnings"])
    return unique(items, limit=8)


def enrich(answer: dict[str, Any]) -> dict[str, Any]:
    active = applies(answer)
    if not active:
        return {
            "active": False,
            "name": "Expert Juriste droit du travail V0 renforce",
            "reason": "Question hors perimetre juriste pour cette orchestration.",
        }

    response = short_response(answer)
    established = established_points(answer)
    depends = depends_on_local_texts(answer)
    reasoning = legal_reasoning(answer)
    sources = source_documents(answer)
    risks = vigilance_points(answer)
    position = proposed_position(answer)
    expert_limits = limits(answer)

    return {
        "active": True,
        "name": "Expert Juriste droit du travail V0 renforce",
        "response_courte": response,
        "reponse_courte": response,
        "qualification_juridique_situation": qualification(answer),
        "ce_qui_est_certain": established,
        "ce_qui_est_etabli_par_sources": established,
        "ce_qui_depend_des_textes_locaux": depends,
        "ce_qui_depend_accord_statut_element_manquant": depends,
        "sources_a_verifier": sources,
        "sources_utilisees": sources,
        "raisonnement_juridique_prudent": reasoning,
        "analyse_et_raisonnement": reasoning,
        "risques_points_vigilance": risks,
        "position_de_travail_proposee": position,
        "questions_a_poser_direction": direction_questions(answer),
        "niveau_de_confiance": answer.get("confidence", "a verifier"),
        "limites": expert_limits,
    }
