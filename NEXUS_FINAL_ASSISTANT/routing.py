"""Contextual, deterministic multi-domain detection."""

from __future__ import annotations

from dataclasses import dataclass

from .models import AssistantRequest, Confidence, Domain, DomainMatch
from .normalization import normalize_text


@dataclass(frozen=True, slots=True)
class DomainRule:
    domain: Domain
    engine: str
    markers: tuple[str, ...]
    route_hints: tuple[str, ...]
    contrary: tuple[str, ...] = ()


_RULES = (
    DomainRule(Domain.CONTRACT, "syndical_reasoning", ("contrat", "avenant", "modification", "poste", "mobilite"), ("contrat_travail",)),
    DomainRule(Domain.DISCIPLINE, "syndical_reasoning", ("sanction", "avertissement", "mise a pied", "entretien prealable", "faute"), ("disciplinaire", "disciplinary_procedure")),
    DomainRule(Domain.WORKING_TIME, "syndical_reasoning", ("horaire", "heures supplementaires", "astreinte", "repos", "poste", "nuit", "5x8"), ("temps_travail",)),
    DomainRule(Domain.DISCRIMINATION, "syndical_reasoning", ("harcelement", "discrimination", "traitement different", "liberte syndicale"), ("discrimination",)),
    DomainRule(Domain.HEALTH, "syndical_reasoning", ("arret maladie", "maladie", "inaptitude", "reclassement", "ijss", "accident du travail"), ("maladie", "absence", "inaptitude", "protection_sociale", "at_mp")),
    DomainRule(Domain.CSE_CONSULTATION, "syndical_reasoning", ("reorganisation", "projet important", "consultation", "information consultation"), ("reorganisation",)),
    DomainRule(Domain.CSE_OPERATION, "syndical_reasoning", ("ordre du jour", "reunion cse", "avis cse", "proces verbal", "pv cse"), ("cse",), ("alerte", "expertise")),
    DomainRule(Domain.CSE_ALERTS, "syndical_reasoning", ("alerte", "expertise", "reclamation collective", "enquete cse", "danger grave"), ("cse",)),
    DomainRule(Domain.PAYROLL, "expert_paie_v2", ("paie", "bulletin", "salaire", "rubrique", "kelio", "nibelis", "compteur"), ("paie_remuneration",)),
    DomainRule(Domain.DOCUMENTARY, "documentary", ("document", "accord", "convention", "source", "ancien pv", "historique"), ("recherche_documentaire",)),
)


class DomainDetector:
    def detect(self, request: AssistantRequest) -> tuple[DomainMatch, ...]:
        text = normalize_text(" ".join((request.question, *(fact.statement for fact in request.facts))))
        hints = {normalize_text(item) for item in request.route_domains}
        matches: list[DomainMatch] = []
        for rule in _RULES:
            triggers = tuple(marker for marker in rule.markers if marker in text)
            route_hits = tuple(marker for marker in rule.route_hints if normalize_text(marker) in hints)
            contrary = tuple(marker for marker in rule.contrary if marker in text)
            score = min(100, len(triggers) * 24 + len(route_hits) * 35 + (12 if request.collective_case and rule.domain.value.startswith("cse_") else 0) - len(contrary) * 12)
            if rule.domain is Domain.DISCRIMINATION and (
                "harcelement" in text or "discrimination" in text
            ):
                score += 30
            if rule.domain is Domain.WORKING_TIME and "heures supplementaires" in text:
                score += 26
            if rule.domain is Domain.CSE_ALERTS and (
                request.collective_case or "collectif" in text
            ) and "alerte" in text:
                score += 36
            score = min(100, score)
            if score <= 0:
                continue
            confidence = Confidence.HIGH if score >= 60 else Confidence.MEDIUM if score >= 30 else Confidence.LOW
            matches.append(
                DomainMatch(
                    rule.domain,
                    score,
                    tuple(dict.fromkeys((*triggers, *route_hits))),
                    contrary,
                    confidence,
                    "candidate",
                    rule.engine,
                    "Indices contextuels et routage existant concordants.",
                )
            )
        if not matches:
            matches.append(
                DomainMatch(
                    Domain.TRANSVERSAL,
                    10,
                    ("question_non_classee",),
                    (),
                    Confidence.LOW,
                    "primary",
                    "syndical_reasoning",
                    "Aucun domaine spécialisé suffisamment étayé.",
                )
            )
        matches.sort(key=lambda item: (-item.score, item.domain.value))
        return tuple(
            DomainMatch(
                item.domain,
                item.score,
                item.triggers,
                item.contrary_indicators,
                item.confidence,
                "primary" if index == 0 else "complementary",
                item.proposed_engine,
                item.selection_reason,
                item.exclusion_reason,
            )
            for index, item in enumerate(matches)
        )
