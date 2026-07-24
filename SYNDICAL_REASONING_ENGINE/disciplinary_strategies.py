"""Ordered and progressive strategies for disciplinary cases."""

from __future__ import annotations

from .contract_change_models import ContractChangeStrategy
from .disciplinary_models import ProtectedEmployeeAnalysis
from .models import SyndicalCaseInput, UrgencyLevel


def build_disciplinary_strategies(
    case: SyndicalCaseInput,
    protection: ProtectedEmployeeAnalysis,
) -> tuple[ContractChangeStrategy, ...]:
    urgency = case.urgency if case.urgency != UrgencyLevel.ROUTINE else UrgencyLevel.PROMPT
    strategies = [
        ContractChangeStrategy(1, "Demander et sécuriser les pièces", "Fixer la chronologie, la mesure et les preuves invoquées.", ("réduit l'incertitude", "préserve les traces"), ("certaines pièces peuvent ne pas être communicables immédiatement",), ("ne suspend pas automatiquement un délai",), ("convocation", "notification", "règlement intérieur"), urgency),
        ContractChangeStrategy(2, "Assister et préparer le salarié", "Préparer l'entretien et une présentation factuelle des observations.", ("garantit une expression structurée",), ("nécessite un temps de préparation",), ("éviter toute affirmation non vérifiée",), ("chronologie", "témoignages", "écrits"), urgency),
        ContractChangeStrategy(3, "Demander des explications motivées", "Obtenir la qualification, les motifs et le cadre invoqués par l'employeur.", ("clarifie la position de l'employeur",), ("la réponse peut rester contestée",), ("surveiller les délais",), ("questions écrites", "compte rendu"), urgency),
        ContractChangeStrategy(4, "Solliciter un réexamen par la direction", "Rechercher une solution proportionnée ou la levée d'une irrégularité.", ("peut éviter une escalade",), ("aucune issue favorable garantie",), ("ne pas renoncer implicitement à un recours",), ("dossier contradictoire",), UrgencyLevel.PROMPT),
        ContractChangeStrategy(5, "Contester formellement la sanction", "Formaliser les moyens factuels, procéduraux et de proportionnalité.", ("préserve une contestation explicite",), ("exige des moyens précis",), ("relation de travail potentiellement plus conflictuelle",), ("courrier motivé", "preuves", "sources vérifiées"), urgency),
    ]
    if protection.protection_possible:
        strategies.append(
            ContractChangeStrategy(6, "Vérifier la saisine de l'inspection du travail", "Sécuriser la procédure propre au salarié potentiellement protégé.", ("évite d'ignorer une garantie administrative",), ("la nécessité de l'autorisation dépend de la mesure et du mandat",), ("aucune conclusion automatique sur la compétence ou l'issue",), ("mandat", "dates de protection", "mesure envisagée"), UrgencyLevel.URGENT)
        )
    strategies.append(
        ContractChangeStrategy(len(strategies) + 1, "Préparer un recours adapté", "Évaluer un recours prud'homal ou toute voie compétente avec un conseil qualifié.", ("préserve une voie externe",), ("coût, délai et aléa",), ("agir sur une qualification ou des preuves incomplètes",), ("dossier complet", "chronologie", "sources à jour"), urgency)
    )
    return tuple(strategies)
