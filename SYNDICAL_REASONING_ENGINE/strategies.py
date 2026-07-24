"""Progressive, non-confrontational action strategy construction."""

from __future__ import annotations

from .models import ActionOption, ActionPlanStep, SyndicalCaseInput, UrgencyLevel


def build_action_options(
    case: SyndicalCaseInput,
    domains: tuple[str, ...],
) -> tuple[ActionOption, ...]:
    options = [
        ActionOption(
            "Clarifier les faits par écrit",
            "Obtenir une décision, sa date, son auteur et son périmètre.",
            "Salarié accompagné du délégué syndical",
            (),
            ("instruction ou proposition écrite", "contrat et avenants"),
            ("réduit l'incertitude", "préserve une trace"),
            ("peut nécessiter une relance",),
            ("ne suspend pas les délais applicables",),
            UrgencyLevel.PROMPT,
            True,
            1,
            "demande_de_precisions",
        ),
        ActionOption(
            "Réunir et comparer les sources",
            "Identifier la règle applicable avant toute prise de position.",
            "Délégué syndical",
            ("faits clarifiés",),
            ("accords applicables", "convention collective", "planning", "bulletins"),
            ("sécurise l'analyse", "identifie les écarts"),
            ("analyse provisoire si une pièce manque",),
            ("une source peut être inapplicable ou obsolète",),
            UrgencyLevel.PROMPT,
            True,
            2,
        ),
        ActionOption(
            "Organiser un échange contradictoire",
            "Présenter les questions et rechercher une solution protectrice.",
            "Délégué syndical et direction",
            ("mandat du salarié", "dossier factuel"),
            ("questions écrites", "pièces pertinentes"),
            ("peut résoudre rapidement", "limite l'escalade"),
            ("ne suspend pas nécessairement un délai",),
            ("position de la direction encore inconnue",),
            UrgencyLevel.PROMPT,
            True,
            3,
            "courrier_de_demande_entretien",
        ),
    ]
    if "cse_consultation" in domains:
        options.append(
            ActionOption(
                "Vérifier la saisine du CSE",
                "Contrôler les obligations d'information ou de consultation.",
                "Élus CSE",
                ("dimension collective établie",),
                ("projet de réorganisation", "ordre du jour", "PV antérieurs"),
                ("permet une analyse collective",),
                ("la compétence du CSE doit être vérifiée",),
                ("calendrier de consultation à confirmer",),
                UrgencyLevel.PROMPT,
                True,
                4,
                "question_ordre_du_jour",
            )
        )
    if "health_safety" in domains:
        options.append(
            ActionOption(
                "Saisir les acteurs de prévention",
                "Évaluer et prévenir les impacts santé-sécurité.",
                "CSE/CSSCT ou service de prévention compétent",
                ("risque documenté ou signalé",),
                ("évaluation des risques", "contraintes de poste"),
                ("protège la santé",),
                ("choisir le dispositif adapté à la gravité",),
                ("ne pas retarder une mesure d'urgence nécessaire",),
                case.urgency,
                True,
                5,
            )
        )
    return tuple(options)


def chronological_plan(options: tuple[ActionOption, ...]) -> tuple[ActionPlanStep, ...]:
    return tuple(
        ActionPlanStep(
            item.recommended_order,
            item.name,
            item.competent_actor,
            "Après vérification des prérequis et des délais applicables.",
        )
        for item in sorted(options, key=lambda value: value.recommended_order)
    )
