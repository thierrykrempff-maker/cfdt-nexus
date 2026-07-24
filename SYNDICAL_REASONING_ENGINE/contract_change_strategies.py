"""Five ordered strategies for contract-change cases."""

from __future__ import annotations

from .contract_change_models import ContractChangeStrategy
from .models import SyndicalCaseInput, UrgencyLevel


def build_contract_change_strategies(
    case: SyndicalCaseInput,
) -> tuple[ContractChangeStrategy, ...]:
    urgency = (
        case.urgency
        if case.urgency in {UrgencyLevel.URGENT, UrgencyLevel.IMMEDIATE}
        else UrgencyLevel.PROMPT
    )
    return (
        ContractChangeStrategy(
            1,
            "Obtenir toutes les informations",
            "Clarifier le projet, sa date, sa durée et ses effets.",
            ("réduit l'incertitude", "préserve une trace"),
            ("nécessite une réponse précise de l'employeur",),
            ("ne suspend pas un délai",),
            ("décision écrite",),
            urgency,
        ),
        ContractChangeStrategy(
            2,
            "Demander et comparer les documents",
            "Comparer contrat, accords, fonctions, horaires et rémunération.",
            ("sécurise la qualification",),
            ("des pièces peuvent manquer",),
            ("une source peut être inapplicable ou obsolète",),
            ("contrat", "avenants", "accords", "planning"),
            urgency,
        ),
        ContractChangeStrategy(
            3,
            "Rencontrer la direction",
            "Exposer les questions et rechercher une solution protectrice.",
            ("permet un échange rapide", "peut éviter une escalade"),
            ("la position de la direction reste à formaliser",),
            ("ne pas renoncer implicitement à un droit",),
            ("dossier factuel", "questions écrites"),
            UrgencyLevel.PROMPT,
        ),
        ContractChangeStrategy(
            4,
            "Préparer une intervention CSE",
            "Traiter la dimension collective ou organisationnelle du projet.",
            ("mobilise les informations collectives",),
            ("la compétence du CSE doit être vérifiée",),
            ("respecter le calendrier applicable",),
            ("projet de réorganisation", "ordre du jour", "PV antérieurs"),
            UrgencyLevel.PROMPT,
        ),
        ContractChangeStrategy(
            5,
            "Préparer un recours adapté",
            "Préserver les droits si la clarification et le dialogue ne suffisent pas.",
            ("préserve une voie de contestation",),
            ("nécessite une qualification et des preuves suffisantes",),
            ("coût, délai et conflictualité à évaluer",),
            ("chronologie", "preuves", "sources vérifiées"),
            urgency,
        ),
    )
