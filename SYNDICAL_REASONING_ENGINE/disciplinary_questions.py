"""Prioritized questions for disciplinary cases."""

from __future__ import annotations

from .contract_change_models import PrioritizedQuestion
from .disciplinary_models import (
    DisciplinaryQualification,
    DisciplinaryQualificationCandidate,
)
from .models import SyndicalCaseInput


def build_disciplinary_questions(
    case: SyndicalCaseInput,
    candidates: tuple[DisciplinaryQualificationCandidate, ...],
) -> tuple[PrioritizedQuestion, ...]:
    known_types = {item.document_type for item in case.available_pieces}
    qualifications = {item.qualification for item in candidates}
    questions: list[PrioritizedQuestion] = []

    def add(priority: int, question: str, purpose: str) -> None:
        questions.append(PrioritizedQuestion(priority, question, purpose))

    add(1, "Quelle est la nature exacte de la mesure annoncée ou notifiée ?", "Distinguer mesure disciplinaire, rappel à l'ordre et autre mesure.")
    add(1, "Quelle est la date précise des faits reprochés ?", "Établir la chronologie et vérifier les délais.")
    add(1, "Quand l'employeur a-t-il eu connaissance des faits ?", "Apprécier le point de départ du délai disciplinaire.")
    add(1, "Les faits sont-ils reconnus, partiellement reconnus ou contestés ?", "Séparer faits établis, déclarés et contestés.")
    if "meeting_invitation" not in known_types:
        add(1, "Quand et comment le salarié a-t-il été convoqué ?", "Vérifier la convocation et son objet.")
    add(1, "Le salarié était-il assisté lors de l'entretien ?", "Vérifier les garanties d'assistance.")
    if "sanction_letter" not in known_types:
        add(1, "Existe-t-il une notification écrite et précisément motivée ?", "Connaître la mesure, ses motifs et sa date.")
    add(2, "Existe-t-il des témoins ou des écrits contemporains des faits ?", "Identifier les preuves disponibles.")
    add(2, "La sanction paraît-elle proportionnée aux faits allégués ?", "Comparer gravité, contexte et mesure envisagée.")
    add(2, "Des situations similaires ont-elles donné lieu à des mesures comparables ?", "Rechercher une cohérence de traitement sans préjuger du résultat.")
    add(2, "Le règlement intérieur prévoit-il cette sanction et la procédure applicable ?", "Vérifier le cadre interne.")
    if DisciplinaryQualification.PROTECTED_EMPLOYEE in qualifications:
        add(1, "Quel mandat ou quelle protection particulière le salarié détient-il ?", "Identifier la protection applicable et sa durée.")
        add(1, "Une autorisation de l'inspection du travail est-elle susceptible d'être requise ?", "Vérifier la procédure administrative sans la présumer.")
    if qualifications.intersection(
        {
            DisciplinaryQualification.PROFESSIONAL_INSUFFICIENCY,
            DisciplinaryQualification.INSUFFICIENT_RESULTS,
        }
    ):
        add(2, "Les objectifs, moyens, compétences attendues et alertes antérieures sont-ils documentés ?", "Distinguer insuffisance, faute et moyens insuffisants.")
    if DisciplinaryQualification.REFUSAL_CONTRACT_CHANGE in qualifications:
        add(2, "Quel changement contractuel a été proposé et le salarié l'a-t-il refusé explicitement ?", "Distinguer refus contractuel et insubordination alléguée.")
    add(3, "Quels accords INEOS et dispositions conventionnelles sont applicables ?", "Identifier les garanties conventionnelles.")
    add(3, "Existe-t-il une jurisprudence réellement comparable et à jour ?", "Éviter une analogie non vérifiée.")
    unique = {(item.question, item.purpose): item for item in questions}
    return tuple(sorted(unique.values(), key=lambda item: (item.priority, item.question)))
