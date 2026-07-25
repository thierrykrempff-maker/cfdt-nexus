"""Prioritized questions for contract and working-condition changes."""

from __future__ import annotations

from .contract_change_models import ChangeDimension, PrioritizedQuestion
from .models import SyndicalCaseInput


def build_questions(
    case: SyndicalCaseInput,
    dimensions: tuple[ChangeDimension, ...],
) -> tuple[PrioritizedQuestion, ...]:
    known_types = {item.document_type for item in case.available_pieces}
    candidates = []

    def add(priority: int, question: str, purpose: str) -> None:
        candidates.append(PrioritizedQuestion(priority, question, purpose))

    if "employment_contract" not in known_types:
        add(1, "Que prévoit précisément le contrat de travail ?", "Identifier les clauses contractualisées.")
    if "amendment" not in known_types:
        add(1, "Existe-t-il un avenant proposé ou signé ?", "Vérifier une modification formalisée.")
    add(1, "Le salarié a-t-il donné un accord explicite et traçable ?", "Distinguer information, proposition et accord.")
    add(2, "Le changement est-il temporaire ou durable ?", "Apprécier la portée et la stabilité du changement.")
    if ChangeDimension.GEOGRAPHIC_MOBILITY in dimensions:
        add(2, "Existe-t-il une clause de mobilité et quel est son périmètre ?", "Vérifier le fondement invoqué.")
    if {
        ChangeDimension.WORKING_HOURS,
        ChangeDimension.DAY_TO_SHIFT,
        ChangeDimension.TEAM,
    }.intersection(dimensions):
        add(2, "Quels horaires, cycles, repos et équipes changent exactement ?", "Mesurer l'écart avant/après.")
        add(2, "Le travail posté est-il prévu au contrat ou par un accord applicable ?", "Identifier le cadre contractuel ou collectif.")
    if ChangeDimension.DAY_TO_SHIFT in dimensions:
        add(1, "Le contrat prévoit-il un travail de jour ou autorise-t-il un rythme posté ?", "Vérifier le cadre contractuel exact.")
        add(1, "Le changement est-il temporaire ou permanent ?", "Qualifier sa durée sans supposer un accord.")
        add(1, "Quel est le cycle exact : matins, après-midis, nuits, week-ends, jours fériés et repos ?", "Objectiver toutes les contraintes temporelles.")
        add(1, "Quelle date de début et quel délai de prévenance ont été annoncés ?", "Préparer la chronologie et les démarches.")
        add(1, "Des volontaires ont-ils été recherchés et pourquoi cette salariée a-t-elle été choisie ?", "Vérifier les critères de choix sans présumer le volontariat.")
        add(1, "Quelles contraintes personnelles, familiales, de transport ou de santé doivent être prises en compte, sans diagnostic médical ?", "Documenter les effets concrets avec prudence.")
    if ChangeDimension.REMUNERATION in dimensions:
        add(2, "Le changement modifie-t-il le salaire, les primes ou accessoires ?", "Identifier un impact de rémunération.")
    if {
        ChangeDimension.POSITION,
        ChangeDimension.QUALIFICATION,
        ChangeDimension.CLASSIFICATION,
    }.intersection(dimensions):
        add(2, "Les missions, responsabilités, qualification ou classification changent-elles ?", "Comparer les fonctions réelles.")
    if ChangeDimension.REORGANIZATION in dimensions:
        add(2, "D'autres salariés sont-ils concernés par le même projet ?", "Évaluer la dimension collective.")
        add(2, "Le CSE a-t-il été informé ou consulté et sur quel projet ?", "Vérifier la procédure collective.")
        add(2, "L'effectif du laboratoire ou de l'équipe de jour sera-t-il durablement réduit ?", "Objectiver la réorganisation et la charge.")
    add(3, "Quels accords INEOS et dispositions de la Convention Chimie sont applicables ?", "Comparer les normes conventionnelles.")
    add(3, "Quelle date d'effet et quel délai de réponse ont été annoncés ?", "Préserver les délais et organiser l'action.")
    unique = {(item.question, item.purpose): item for item in candidates}
    return tuple(
        sorted(unique.values(), key=lambda item: (item.priority, item.question))
    )
