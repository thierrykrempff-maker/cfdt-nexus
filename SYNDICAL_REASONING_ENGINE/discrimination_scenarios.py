"""Twelve anonymous and synthetic R1D reference scenarios."""

from __future__ import annotations

from .models import CaseFact, SyndicalCaseInput, UrgencyLevel


def _case(question: str, facts: tuple[str, ...], domains=("discrimination",), urgency=UrgencyLevel.ROUTINE) -> SyndicalCaseInput:
    return SyndicalCaseInput(
        question=question,
        declared_facts=tuple(CaseFact(item) for item in facts),
        suspected_domains=domains,
        urgency=urgency,
    )


def discrimination_harassment_scenarios() -> dict[str, SyndicalCaseInput]:
    return {
        "possible_moral_harassment": _case("Critiques répétées, retrait progressif de missions et isolement.", ("Des critiques sont déclarées plusieurs fois.", "Des missions auraient été retirées progressivement.")),
        "isolated_conflict": _case("Une remarque déplacée unique pendant une réunion.", ("Un événement isolé est déclaré.",)),
        "possible_sexual_harassment": _case("Messages répétés à connotation sexuelle.", ("Plusieurs messages sont déclarés.",), urgency=UrgencyLevel.URGENT),
        "union_discrimination": _case("Après un mandat syndical, stagnation de carrière face à des comparateurs.", ("Une évolution différente est déclarée après le mandat.",)),
        "equal_pay": _case("Différence de rémunération entre deux salariés.", ("Les fonctions et responsabilités restent à comparer.",), ("discrimination", "paie_remuneration")),
        "health_return": _case("Après un retour d'arrêt maladie, retrait de missions.", ("Une adaptation temporaire ou une mesure défavorable reste à distinguer.",)),
        "retaliation": _case("Évaluation défavorable peu après avoir signalé des faits.", ("La proximité temporelle est déclarée.",)),
        "different_sanctions": _case("Deux salariés pour des faits similaires, un seul sanctionné lourdement.", ("La comparabilité et les antécédents sont inconnus.",), ("discrimination", "disciplinary_procedure")),
        "sexist_behaviour": _case("Remarques sexistes répétées liées au sexe sans sollicitation sexuelle.", ("Les propos exacts restent à documenter.",)),
        "insufficient_evidence": _case("Sentiment de discrimination sans fait précis ni comparateur.", ("Le ressenti doit être accueilli sans confirmation juridique.",)),
        "representative_isolated": _case("Un élu CSE perd progressivement dossiers, réunions et perspectives.", ("Le lien avec le mandat reste à examiner.",), ("droit_syndical", "discrimination")),
        "immediate_danger": _case("Une violence imminente et un danger immédiat sont déclarés.", ("La mise en sécurité est prioritaire.",), urgency=UrgencyLevel.IMMEDIATE),
    }
