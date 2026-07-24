"""Fifteen anonymous and fully synthetic R2A scenarios."""

from __future__ import annotations

from .models import CaseFact, SyndicalCaseInput, UrgencyLevel


def _case(question: str, *facts: str) -> SyndicalCaseInput:
    return SyndicalCaseInput(
        question,
        declared_facts=tuple(CaseFact(item) for item in facts),
        person_capacity="élu ou délégué syndical fictif",
        workplace_context="établissement synthétique sans donnée réelle",
        suspected_domains=("cse", "cse_consultation"),
        urgency=UrgencyLevel.PROMPT,
        desired_outcome="qualifier prudemment le projet et préparer une démarche graduée",
        missing_information=("chronologie certaine", "documents transmis", "impacts détaillés"),
    )


def cse_consultation_scenarios() -> dict[str, SyndicalCaseInput]:
    return {
        "laboratory": _case("Une personne de jour passe en équipe postée et plusieurs changements similaires sont annoncés.", "Le changement individuel est déclaré.", "D'autres cas sont annoncés."),
        "job_suppression": _case("Une réorganisation supprime plusieurs postes sans document complet transmis au CSE.", "Plusieurs postes seraient concernés."),
        "collective_schedule": _case("Plusieurs équipes changent de cycle et d'horaires.", "La décision est annoncée."),
        "monitoring_tool": _case("Un nouvel outil de contrôle et logiciel de suivi est introduit.", "Le dispositif concernerait un service."),
        "outsourcing": _case("Un projet d'externalisation confie une activité à un prestataire.", "Plusieurs salariés seraient concernés."),
        "employees_informed_first": _case("Les salariés sont informés d'un projet avant le CSE.", "La décision définitive reste inconnue."),
        "implementation_before_opinion": _case("La mise en œuvre a commencé avant avis ; la consultation reste à vérifier.", "Un changement collectif est déclaré."),
        "insufficient_documents": _case("Le CSE a été informé mais reçoit une présentation générale sans données d'impact.", "Les documents sont insuffisants selon les élus."),
        "isolated_individual": _case("Un seul salarié change de poste, sans autre indice collectif.", "Le cas paraît individuel et isolé."),
        "repeated_individual": _case("Plusieurs changements similaires apparaissent progressivement dans le même service.", "Une répétition de cas individuels est déclarée."),
        "historical_commitment": _case("Un ancien PV CSE pourrait contenir un engagement pertinent sur ce projet.", "Le contenu source n'est pas disponible."),
        "economic_project": _case("Un projet économique affecte les effectifs, l'organisation et les compétences.", "Plusieurs salariés seraient concernés."),
        "document_refusal": _case("La direction oppose la confidentialité et refuse des documents sur une réorganisation.", "Le CSE demande les impacts."),
        "regular_consultation": _case("Le CSE a été consulté, a reçu les documents, posé des questions et rendu un avis avant mise en œuvre.", "La consultation réalisée est documentée."),
        "obstruction_risk": _case("Une mise en œuvre a commencé sans consultation connue et des documents sont refusés.", "Plusieurs indices existent mais les faits restent incomplets."),
    }
