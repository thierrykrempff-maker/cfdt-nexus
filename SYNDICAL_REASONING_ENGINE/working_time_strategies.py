"""Five graduated R1C strategies."""

from __future__ import annotations

from .models import SyndicalCaseInput, UrgencyLevel
from .working_time_models import WorkingTimeStrategy


def build_working_time_strategies(
    case: SyndicalCaseInput,
) -> tuple[WorkingTimeStrategy, ...]:
    urgency = case.urgency if case.urgency != UrgencyLevel.ROUTINE else UrgencyLevel.PROMPT
    return (
        WorkingTimeStrategy(1, "Sécurisation factuelle", "Reconstituer la chronologie et réunir les relevés.", urgency, ("préserve les traces", "réduit l'incertitude"), ("certaines pièces dépendent de l'employeur",), ("ne pas déduire une durée de données incomplètes",), ("planning", "badgeages", "dates et heures"), "chronologie vérifiable", "passer à la comparaison documentaire"),
        WorkingTimeStrategy(2, "Comparaison structurée", "Rapprocher planning, Kelio, interventions, repos et bulletin.", urgency, ("localise les écarts", "teste les explications alternatives"), ("ne constitue pas un calcul de paie",), ("confondre périodes ou mécanismes de compensation",), ("cycle", "Kelio", "Nibelis", "accord"), "écarts et concordances documentés", "demander une explication interne"),
        WorkingTimeStrategy(3, "Demande interne", "Obtenir une explication, une vérification de compteur, de repos ou de paie.", urgency, ("peut corriger rapidement une anomalie",), ("réponse ou correction non garantie",), ("surveiller les délais et conserver les échanges",), ("dossier comparatif", "demande écrite"), "réponse motivée ou contrôle interne", "organiser une action syndicale"),
        WorkingTimeStrategy(4, "Action syndicale ou collective", "Porter le dossier avec le délégué syndical ou au CSE si plusieurs salariés sont concernés.", UrgencyLevel.PROMPT, ("permet une analyse collective", "compare des situations homogènes"), ("la dimension collective doit être établie",), ("respecter la confidentialité individuelle",), ("cas anonymisés", "règles collectives", "écarts récurrents"), "traitement collectif ou engagement de vérification", "évaluer un recours adapté"),
        WorkingTimeStrategy(5, "Recours adapté", "Évaluer inspection du travail, contestation écrite, conseil juridique ou recours prud'homal.", urgency, ("préserve une voie externe",), ("coût, délai et aléa",), ("agir avec une qualification ou des preuves insuffisantes",), ("chronologie", "pièces", "sources à jour"), "orientation vers la voie compétente", "faire réévaluer le dossier par un professionnel"),
    )
