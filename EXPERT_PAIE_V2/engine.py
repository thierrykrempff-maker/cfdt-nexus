"""Operational orchestration for controlled, explainable payroll checks."""

from __future__ import annotations

from .calculation import calculate
from .comparisons import compare_payload
from .models import (
    ComparisonStatus,
    ConfidenceLevel,
    EvidencePriority,
    PayrollEvidence,
    PayrollPhase,
    PayrollQuestion,
    PayrollStrategy,
    PayrollV2Analysis,
    PayrollV2Input,
    QuestionPriority,
)
from .rules import select_rules, selected_rule
from .validation import validate_calculation


class ExpertPaieV2Engine:
    def analyze(
        self, payload: PayrollV2Input, *, scenario_code: str | None = None
    ) -> PayrollV2Analysis:
        if not isinstance(payload, PayrollV2Input):
            raise TypeError("payload must be PayrollV2Input")
        selections = select_rules(payload.events, payload.rules)
        rule = selected_rule(payload.rules, selections)
        if rule is None:
            event_types = {item.event_type for item in payload.events}
            rule = next(
                (
                    item
                    for item in payload.rules
                    if event_types.intersection(item.event_types)
                ),
                None,
            )
        comparisons = compare_payload(payload, rule)
        refusals = validate_calculation(
            payload,
            rule,
            applicable_rule_count=sum(item.selected for item in selections),
        )
        calculation = None
        if not refusals and rule is not None:
            calculation = calculate(payload, rule)
            phase = PayrollPhase.AUTHORIZED_CALCULATION
        elif payload.events and (payload.kelio_counters or payload.nibelis_rubrics):
            phase = PayrollPhase.CALCULATION_REFUSED
        elif payload.events:
            phase = PayrollPhase.CONTROL
        else:
            phase = PayrollPhase.DETECTION
        confidence = _confidence(payload, comparisons, refusals)
        alternatives = tuple(
            dict.fromkeys(
                alternative
                for comparison in comparisons
                for alternative in comparison.alternative_explanations
            )
        )
        return PayrollV2Analysis(
            phase,
            payload.events,
            selections,
            comparisons,
            calculation,
            refusals,
            alternatives,
            _questions(payload, rule),
            _evidence(),
            _strategies(),
            _employee_explanation(comparisons, refusals),
            _expert_explanation(selections, comparisons, refusals, calculation),
            _articulation(payload),
            confidence,
            scenario_code,
        )


def _questions(payload, rule):
    known = set(payload.available_documents)
    rows = (
        (QuestionPriority.CRITICAL, "Quelle période de paie est concernée ?", "délimiter le contrôle", "periode"),
        (QuestionPriority.CRITICAL, "Quel était le planning prévu et quelles heures ont été effectuées ?", "reconstituer l'événement", "planning"),
        (QuestionPriority.CRITICAL, "Quel compteur Kelio et quelle rubrique Nibelis sont concernés ?", "rapprocher temps et paie", "kelio_nibelis"),
        (QuestionPriority.PRIORITY, "Une rubrique ou régularisation figure-t-elle sur le mois suivant ?", "éviter une fausse anomalie", "regularisation"),
        (QuestionPriority.PRIORITY, "Quel accord INEOS ou quelle autre source applicable régit l'événement ?", "sélectionner la règle", "accord"),
        (QuestionPriority.PRIORITY, "La règle et le calcul sont-ils explicitement autorisés ?", "bloquer un calcul non permis", "regle"),
        (QuestionPriority.USEFUL, "Pour une astreinte, intervention et déplacement sont-ils distingués ?", "séparer les événements", "astreinte"),
        (QuestionPriority.USEFUL, "Pour une absence, IJSS, maintien, subrogation et prévoyance sont-ils documentés ?", "rapprocher les flux sans promesse", "maladie"),
        (QuestionPriority.COMPLEMENTARY, "Le taux, la base, la quantité et leurs unités sont-ils connus ?", "sécuriser le calcul", "variables"),
    )
    return tuple(PayrollQuestion(priority, wording, purpose) for priority, wording, purpose, key in rows if key not in known)


def _evidence():
    rows = (
        ("bulletin et période", "observer les rubriques", EvidencePriority.ESSENTIAL),
        ("planning", "établir l'événement prévu", EvidencePriority.ESSENTIAL),
        ("compteur Kelio", "établir l'événement enregistré", EvidencePriority.ESSENTIAL),
        ("rubrique Nibelis", "observer le traitement", EvidencePriority.ESSENTIAL),
        ("règle et accord applicables", "sécuriser la source", EvidencePriority.ESSENTIAL),
        ("badgeages, contrat, avenant ou intervention", "corroborer", EvidencePriority.USEFUL),
        ("décompte IJSS et historique de paie", "rapprocher les périodes", EvidencePriority.USEFUL),
        ("paramètre applicable", "documenter une variable", EvidencePriority.USEFUL),
        ("réponse RH ou pratique antérieure", "fournir une explication alternative", EvidencePriority.COMPLEMENTARY),
        ("PV CSE metadata-only", "identifier une dimension collective", EvidencePriority.COMPLEMENTARY),
    )
    return tuple(PayrollEvidence(name, utility, "source synthétique à fournir", priority, "accès limité", "ne prouve pas seul une erreur", utility) for name, utility, priority in rows)


def _strategies():
    rows = (
        (1, "Reconstitution", "identifier période, événements, pièces et compteurs", "salarié / représentant", "dossier structuré", "données manquantes", "mauvaise période", "comparaison"),
        (2, "Comparaison", "rapprocher planning, Kelio, Nibelis et règle", "expert paie / représentant", "écart expliqué", "aucune certitude automatique", "faux positif", "vérification"),
        (3, "Demande de vérification", "obtenir l'explication et le détail du calcul", "service paie", "réponse traçable", "réponse partielle", "retard", "régularisation"),
        (4, "Demande de régularisation", "demander correction motivée si l'écart persiste", "salarié / syndicat", "correction potentielle", "chiffrage seulement si autorisé", "contestation", "recours"),
        (5, "Recours", "solliciter l'acteur compétent", "syndicat / conseil", "examen externe", "procédure à vérifier", "coût et délai", "suivi"),
    )
    return tuple(
        PayrollStrategy(
            level,
            name,
            objective,
            "à apprécier",
            actor,
            ("pièces du contrôle",),
            (adv,),
            (limit,),
            (risk,),
            adv,
            nxt,
        )
        for level, name, objective, actor, adv, limit, risk, nxt in rows
    )


def _employee_explanation(comparisons, refusals):
    return (
        "Le contrôle porte uniquement sur des données synthétiques et documentées.",
        "Aucune erreur de paie n'est tenue pour certaine.",
        "Les écarts apparents doivent être vérifiés avec le bulletin, le planning, Kelio, Nibelis et la règle applicable.",
        "Le calcul est refusé tant qu'une condition obligatoire manque." if refusals else "Un calcul synthétique autorisé reste soumis à validation humaine.",
    )


def _expert_explanation(selections, comparisons, refusals, calculation):
    return (
        f"règles candidates={len(selections)}",
        f"règles retenues={sum(item.selected for item in selections)}",
        f"comparaisons={len(comparisons)}",
        f"refus={','.join(item.code for item in refusals) or 'aucun'}",
        f"calcul={'autorisé' if calculation else 'non exécuté'}",
    )


def _articulation(payload):
    domains = []
    event_types = {item.event_type.value for item in payload.events}
    if event_types.intersection({"overtime", "night_work", "sunday_work", "public_holiday", "on_call", "on_call_intervention", "on_call_travel"}):
        domains.append("R1C qualifie l'événement ; Expert Paie V2 contrôle compteurs et rubriques.")
    if event_types.intersection({"sickness", "work_accident", "salary_maintenance", "ijss", "subrogation", "provident"}):
        domains.append("R1E qualifie l'absence et la protection ; Expert Paie V2 rapproche les données de paie.")
    if payload.source_domain == "collective":
        domains.append("R2C peut traiter la dimension collective à partir des constats structurés.")
    return tuple(domains) or ("Expert Paie V2 reste principal pour le contrôle de paie.",)


def _confidence(payload, comparisons, refusals):
    if refusals:
        return ConfidenceLevel.LOW
    if comparisons and all(item.status in {ComparisonStatus.MATCH, ComparisonStatus.NO_ANOMALY_DETECTED} for item in comparisons):
        return ConfidenceLevel.HIGH
    return ConfidenceLevel.MODERATE
