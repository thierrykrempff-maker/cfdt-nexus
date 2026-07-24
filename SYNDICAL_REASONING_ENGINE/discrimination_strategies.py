"""Five progressive protection strategies for R1D."""

from __future__ import annotations

from .discrimination_models import ProtectionStrategy
from .models import UrgencyLevel


def build_discrimination_strategies(
    urgency: UrgencyLevel,
) -> tuple[ProtectionStrategy, ...]:
    return (
        ProtectionStrategy(1, "Sécurisation", "Protéger la personne, écouter et distinguer faits, ressentis et hypothèses.", urgency, ("réduit le risque immédiat",), ("ne qualifie pas juridiquement"), ("confrontation non préparée à éviter",), ("récit factuel", "contacts utiles"), "représentant syndical et professionnels compétents", "situation sécurisée et faits structurés", "passer à la documentation"),
        ProtectionStrategy(2, "Documentation", "Construire la chronologie, conserver les preuves licites et rechercher des comparateurs.", UrgencyLevel.PROMPT, ("objective les indices",), ("données parfois incomplètes"), ("collecte excessive ou illicite à proscrire",), ("écrits", "évaluations", "comparateurs"), "salarié accompagné", "dossier factuel organisé", "formaliser une protection interne"),
        ProtectionStrategy(3, "Protection interne", "Formaliser le signalement et demander une réponse ou une enquête adaptée.", UrgencyLevel.PROMPT, ("trace la démarche", "permet des mesures conservatoires"), ("impartialité à vérifier",), ("représailles possibles à surveiller",), ("signalement écrit", "chronologie"), "direction, référent, service de prévention ou médecin du travail", "mesures de protection et réponse tracée", "mobiliser les institutions compétentes"),
        ProtectionStrategy(4, "Action collective ou institutionnelle", "Mobiliser les instances et autorités compétentes selon les faits.", UrgencyLevel.PROMPT, ("apporte un cadre collectif ou institutionnel",), ("compétence à vérifier au cas par cas"), ("confidentialité et proportionnalité"), ("dossier factuel", "signalements"), "CSE, inspection du travail ou Défenseur des droits", "examen externe ou action collective proportionnée", "évaluer un recours"),
        ProtectionStrategy(5, "Recours", "Préparer une contestation ou un recours avec un conseil compétent.", UrgencyLevel.ROUTINE, ("préserve les droits",), ("délais, preuve et coût à apprécier"), ("contentieux et exposition de la personne"), ("dossier complet", "preuves licites", "décisions contestées"), "conseil juridique ou juridiction compétente", "stratégie de recours éclairée", "réévaluer le dossier selon les éléments nouveaux"),
    )
