"""Five progressive R1E strategies with explicit competent actors."""

from __future__ import annotations

from .health_absence_models import CompetentActor, HealthStrategy
from .models import UrgencyLevel


def build_health_strategies(urgency: UrgencyLevel) -> tuple[HealthStrategy, ...]:
    return (
        HealthStrategy(1, "Sécurisation", "Établir la chronologie, protéger les données et identifier les échéances.", urgency, CompetentActor.UNION_REPRESENTATIVE, ("réduit les risques immédiats",), ("ne tranche aucun droit"), ("données de santé à minimiser",), ("documents administratifs minimaux",), "dossier sécurisé et échéances identifiées", "passer aux vérifications"),
        HealthStrategy(2, "Vérification", "Comparer transmissions, planning, IJSS, bulletin, accords et garanties sans calcul.", UrgencyLevel.PROMPT, CompetentActor.HR, ("objective les écarts"), ("décalages possibles"), ("conclusion prématurée"), ("métadonnées concordantes",), "écarts expliqués ou documentés", "saisir l'acteur compétent"),
        HealthStrategy(3, "Demande interne ou administrative", "Obtenir une réponse de l'acteur responsable.", UrgencyLevel.PROMPT, CompetentActor.CPAM, ("trace la démarche"), ("délais variables"), ("mauvais destinataire à éviter"), ("demande écrite", "pièces minimales"), "réponse ou instruction formalisée", "engager une action institutionnelle"),
        HealthStrategy(4, "Action syndicale ou institutionnelle", "Accompagner et mobiliser l'instance compétente.", UrgencyLevel.PROMPT, CompetentActor.UNION_REPRESENTATIVE, ("coordonne les acteurs"), ("compétences distinctes"), ("confidentialité"), ("chronologie", "réponses obtenues"), "mesure ou examen adapté", "évaluer le recours"),
        HealthStrategy(5, "Recours", "Préparer une contestation adaptée à la décision et au délai.", UrgencyLevel.ROUTINE, CompetentActor.LEGAL_COUNSEL, ("préserve les voies de recours"), ("preuve et délai à vérifier"), ("contentieux"), ("décision", "dossier factuel"), "recours éclairé", "réévaluer après décision"),
    )
