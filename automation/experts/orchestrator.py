#!/usr/bin/env python
"""First local orchestration layer for Nexus experts."""

from __future__ import annotations

from typing import Any

from . import juriste_travail, paie
from .utils import route_domains, source_documents, unique


CONFIDENCE_ORDER = {"faible": 0, "moyen": 1, "fort": 2}


def lowest_confidence(values: list[str]) -> str:
    cleaned = [value for value in values if value in CONFIDENCE_ORDER]
    if not cleaned:
        return "a verifier"
    return min(cleaned, key=lambda value: CONFIDENCE_ORDER[value])


def active_experts(experts: dict[str, dict[str, Any]]) -> list[str]:
    return [expert["name"] for expert in experts.values() if expert.get("active")]


def build_synthesis(answer: dict[str, Any], juriste: dict[str, Any], paie_expert: dict[str, Any]) -> str:
    domains = route_domains(answer)
    primary_mode = juriste.get("mode_metier_principal")
    if primary_mode == "NEGOCIATION_ACCORD":
        return (
            "Nexus traite la demande comme une preparation de negociation d'accord : comparer le projet aux droits actuels, "
            "identifier pertes, garanties, risques et contre-propositions, puis laisser la decision de signature au delegue syndical."
        )
    if primary_mode == "CSE_CSSCT":
        return (
            "Nexus traite la demande comme un dossier CSE/CSSCT : obtenir les documents utiles, verifier l'information ou consultation, "
            "preparer les questions, les relances et les points a faire acter au proces-verbal."
        )
    if primary_mode == "DEFENSE_SALARIE" and "disciplinaire" in domains:
        return (
            "Nexus traite la demande comme une defense disciplinaire : securiser les faits, les preuves, la procedure, le contexte "
            "de l'erreur et la proportionnalite avant toute conclusion."
        )
    if juriste.get("active") and paie_expert.get("active") and "astreinte" in domains:
        return (
            "Nexus retient une situation mixte : cote droit du travail, il faut qualifier l'astreinte, "
            "l'intervention, le repos et la reprise du poste ; cote paie, il faut controler les heures d'intervention, "
            "les majorations, les recuperations, les compteurs et le bulletin. A ce stade, Nexus ne chiffre pas et ne conclut "
            "pas definitivement sans l'accord applicable, les horaires reels et les bulletins."
        )
    if juriste.get("active") and paie_expert.get("active"):
        return (
            "Nexus mobilise le juriste et la paie : la qualification juridique fixe le cadre, puis la paie controle les "
            "rubriques et les montants. Aucun calcul n'est produit tant que les donnees et les textes applicables ne sont pas complets."
        )
    if paie_expert.get("active"):
        if paie_expert.get("niveau_de_confiance") == "faible":
            return (
                "La question est trop incomplete pour conclure : Nexus identifie un controle paie possible, mais il faut "
                "d'abord preciser la rubrique visee, la periode, le bulletin, la source applicable et les donnees de calcul."
            )
        return (
            "Nexus peut proposer une methode de controle paie, mais pas un calcul fiable sans bulletin detaille, pointage, "
            "compteurs, taux applicable et source locale confirmee."
        )
    if juriste.get("active"):
        return juriste.get("response_courte") or answer.get("short_answer") or "Nexus demande les sources et faits manquants avant conclusion."
    return answer.get("short_answer") or "Nexus n'a pas mobilise d'expert specialise sur cette question."


def build_position(answer: dict[str, Any], juriste: dict[str, Any], paie_expert: dict[str, Any]) -> str:
    if juriste.get("active"):
        return juriste.get("position_de_travail_proposee") or answer.get("working_position", "")
    if paie_expert.get("active") and paie_expert.get("niveau_de_confiance") == "faible":
        return (
            "Position de travail: demander d'abord le libelle exact de la rubrique, la periode et le bulletin concerne, "
            "puis seulement rapprocher la regle applicable et les donnees de calcul."
        )
    return answer.get("working_position", "")


def build_analysis_by_expertise(juriste: dict[str, Any], paie_expert: dict[str, Any]) -> list[dict[str, Any]]:
    analyses: list[dict[str, Any]] = []
    if juriste.get("active"):
        analyses.append(
            {
                "expert": juriste["name"],
                "role": "Qualifier la situation, distinguer regle certaine, interpretation, hypothese et informations manquantes.",
                "synthese": juriste.get("response_courte"),
                "points_cles": unique(
                    [
                        juriste.get("qualification_juridique_situation"),
                        juriste.get("position_de_travail_proposee"),
                        *juriste.get("risques_points_vigilance", [])[:3],
                    ],
                    limit=6,
                ),
            }
        )
    if paie_expert.get("active"):
        analyses.append(
            {
                "expert": paie_expert["name"],
                "role": "Identifier les rubriques, donnees, sources et controles paie sans inventer de calcul.",
                "synthese": paie_expert.get("objet_du_controle"),
                "points_cles": unique(
                    [
                        *paie_expert.get("elements_du_bulletin_concernes", [])[:4],
                        paie_expert.get("calcul_detaille"),
                    ],
                    limit=6,
                ),
            }
        )
    return analyses


def build_documents(answer: dict[str, Any], juriste: dict[str, Any], paie_expert: dict[str, Any]) -> list[str]:
    values: list[str] = []
    values.extend(str(item) for item in answer.get("documents_to_request", []))
    if juriste.get("active"):
        values.extend(str(item) for item in juriste.get("pieces_a_recuperer", []))
    if paie_expert.get("active"):
        values.extend(str(item) for item in paie_expert.get("documents_necessaires", []))
    return unique(values, limit=14)


def build_questions(answer: dict[str, Any], juriste: dict[str, Any], paie_expert: dict[str, Any]) -> list[str]:
    values: list[str] = []
    values.extend(str(item) for item in answer.get("questions_to_ask", []))
    if juriste.get("active"):
        values.extend(str(item) for item in juriste.get("questions_a_poser_direction", []))
    if paie_expert.get("active"):
        values.extend(str(item) for item in paie_expert.get("donnees_necessaires_au_calcul", []))
    return unique(values, limit=12)


def build_limits(answer: dict[str, Any], juriste: dict[str, Any], paie_expert: dict[str, Any]) -> list[str]:
    values: list[str] = []
    values.extend(str(item) for item in answer.get("warnings", []))
    if juriste.get("active"):
        values.extend(str(item) for item in juriste.get("limites", []))
    if paie_expert.get("active"):
        values.extend(str(item) for item in paie_expert.get("limites", []))
    if not values:
        values.append("Nexus reste dependant des sources locales retrouvees par le routeur V1.2.")
    return unique(values, limit=12)


def orchestrate(answer: dict[str, Any]) -> dict[str, Any]:
    juriste = juriste_travail.enrich(answer)
    paie_expert = paie.enrich(answer)
    experts = {"juriste": juriste, "paie": paie_expert}
    mobilized = active_experts(experts)
    confidence_values = [answer.get("confidence", ""), juriste.get("niveau_de_confiance", ""), paie_expert.get("niveau_de_confiance", "")]
    if not mobilized:
        confidence_values = [answer.get("confidence", "")]

    orchestration = {
        "question_posee": answer.get("query", ""),
        "domaines_detectes": [domain for domain in answer.get("route", {}).get("domains", []) if domain != "bible_accords"],
        "mode_metier_principal": juriste.get("mode_metier_principal"),
        "modes_metier": juriste.get("modes_metier", []),
        "experts_mobilises": mobilized,
        "reponse_synthetique_nexus": build_synthesis(answer, juriste, paie_expert),
        "position_de_travail": build_position(answer, juriste, paie_expert),
        "analyse_metier": juriste.get("analyse_metier", []),
        "analyse_par_expertise": build_analysis_by_expertise(juriste, paie_expert),
        "sources": answer.get("sources", []),
        "source_layers": answer.get("source_layers", []),
        "documents_necessaires": build_documents(answer, juriste, paie_expert),
        "questions_utiles": build_questions(answer, juriste, paie_expert),
        "niveau_de_confiance": lowest_confidence(confidence_values),
        "limites": build_limits(answer, juriste, paie_expert),
    }
    return {
        "expert_juriste": juriste,
        "expert_paie": paie_expert,
        "experts": experts,
        "orchestration": orchestration,
    }
