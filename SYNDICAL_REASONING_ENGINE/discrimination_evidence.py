"""Lawful evidence requirements for R1D."""

from __future__ import annotations

from .discrimination_models import EvidenceCategory, EvidenceRequirement
from .models import ConfidenceLevel


def discrimination_evidence() -> tuple[EvidenceRequirement, ...]:
    rows = (
        ("chronology", "Chronologie détaillée", EvidenceCategory.ESSENTIAL, "Structurer les faits et leur enchaînement.", "Dates, répétition et proximité temporelle.", "La qualification juridique finale.", ConfidenceLevel.MODERATE),
        ("messages", "Messages ou courriels concernés", EvidenceCategory.ESSENTIAL, "Conserver les termes et dates exacts.", "Existence et contenu d'un échange.", "L'intention ou l'ensemble du contexte.", ConfidenceLevel.MODERATE),
        ("adverse_decisions", "Décisions défavorables", EvidenceCategory.ESSENTIAL, "Identifier la mesure et son auteur.", "Nature et date de la mesure.", "Son lien avec un critère protégé.", ConfidenceLevel.MODERATE),
        ("appraisals", "Évaluations professionnelles", EvidenceCategory.ESSENTIAL, "Comparer l'évolution documentée.", "Évolution des appréciations.", "Une discrimination sans comparaison homogène.", ConfidenceLevel.MODERATE),
        ("reports_and_responses", "Signalements et réponses de l'employeur", EvidenceCategory.ESSENTIAL, "Évaluer la réaction et les mesures prises.", "Chronologie du signalement et réponse.", "La matérialité de tous les faits signalés.", ConfidenceLevel.MODERATE),
        ("comparison_data", "Données de comparaison homogènes", EvidenceCategory.ESSENTIAL, "Tester une différence de traitement apparente.", "Écarts entre situations comparables.", "Le caractère discriminatoire de l'écart.", ConfidenceLevel.MODERATE),
        ("witness_statements", "Témoignages", EvidenceCategory.USEFUL, "Corroborer des événements observés.", "Ce que le témoin a personnellement constaté.", "Les faits hors de sa présence.", ConfidenceLevel.LOW),
        ("job_description", "Fiche de poste et objectifs", EvidenceCategory.USEFUL, "Comparer missions et responsabilités.", "Cadre attendu du poste.", "Le travail réellement accompli à elle seule.", ConfidenceLevel.MODERATE),
        ("organization_chart", "Organigramme", EvidenceCategory.USEFUL, "Identifier équipe et hiérarchie.", "Structure déclarée.", "La pratique managériale réelle.", ConfidenceLevel.LOW),
        ("career_training", "Historique carrière et formation", EvidenceCategory.USEFUL, "Comparer progression et accès aux opportunités.", "Évolution documentée.", "Le motif d'un écart isolé.", ConfidenceLevel.MODERATE),
        ("collective_indicators", "Indicateurs collectifs et accords", EvidenceCategory.COMPLEMENTARY, "Contextualiser une pratique.", "Tendance ou règle collective.", "Un cas individuel sans faits propres.", ConfidenceLevel.LOW),
        ("cse_metadata", "PV CSE metadata-only", EvidenceCategory.COMPLEMENTARY, "Repérer un sujet collectif ou antérieur.", "Existence, date et thème d'une réunion.", "Le contenu intégral ou la preuve d'un fait individuel.", ConfidenceLevel.LOW),
    )
    return tuple(
        EvidenceRequirement(
            code,
            label,
            category,
            utility,
            can_demonstrate,
            cannot,
            reliability,
            "Obtention licite uniquement ; ne pas contourner un accès ni collecter des données non nécessaires.",
        )
        for code, label, category, utility, can_demonstrate, cannot, reliability in rows
    )
