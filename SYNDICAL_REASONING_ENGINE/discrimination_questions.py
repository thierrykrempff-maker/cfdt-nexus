"""Prioritized, non-redundant questions for R1D."""

from __future__ import annotations

from .discrimination_models import (
    AdverseMeasure,
    PrioritizedQuestion,
    ProtectedCriterion,
    QuestionPriority,
)
from .models import SyndicalCaseInput


def build_discrimination_questions(
    case: SyndicalCaseInput,
    criteria: tuple[ProtectedCriterion, ...],
    measures: tuple[AdverseMeasure, ...],
    *,
    immediate_danger: bool,
) -> tuple[PrioritizedQuestion, ...]:
    known_types = {item.document_type for item in case.available_pieces}
    known_text = " ".join(
        [case.question.lower()]
        + [item.statement.lower() for item in case.declared_facts + case.established_facts]
    )
    questions = []

    def add(priority: QuestionPriority, question: str, purpose: str, marker: str = "") -> None:
        if marker and marker in known_text:
            return
        questions.append(PrioritizedQuestion(priority, question, purpose))

    if immediate_danger:
        add(QuestionPriority.CRITICAL, "La personne est-elle actuellement en sécurité ?", "Prioriser la protection humaine immédiate.")
    add(QuestionPriority.CRITICAL, "Quels faits précis se sont produits et à quelles dates ?", "Distinguer les faits des interprétations.", "faits precis")
    add(QuestionPriority.CRITICAL, "Existe-t-il une menace, une violence ou un danger immédiat ?", "Évaluer l'urgence sans poser de diagnostic.", "danger immediat")
    add(QuestionPriority.PRIORITY, "Les faits sont-ils répétés et sur quelle durée ?", "Documenter répétition et continuité.", "repete")
    add(QuestionPriority.PRIORITY, "Qui était présent et existe-t-il des témoins ?", "Identifier des sources factuelles.", "temoin")
    if "messages" not in known_types and "email" not in known_types:
        add(QuestionPriority.PRIORITY, "Existe-t-il des messages, courriels ou écrits conservés ?", "Recenser les preuves obtenues licitement.")
    if not measures:
        add(QuestionPriority.PRIORITY, "Une mesure défavorable a-t-elle été prise ?", "Identifier l'acte à comparer.")
    if not criteria:
        add(QuestionPriority.PRIORITY, "Quel critère protégé pourrait être concerné, sans présumer du lien causal ?", "Identifier une hypothèse à vérifier.")
    add(QuestionPriority.PRIORITY, "Existe-t-il des salariés placés dans une situation réellement comparable ?", "Éviter les comparaisons simplistes.", "comparateur")
    add(QuestionPriority.USEFUL, "Les faits ont-ils été signalés, à qui et sous quelle forme ?", "Établir la chronologie du signalement.", "signale")
    add(QuestionPriority.USEFUL, "Quelle réponse l'employeur a-t-il apportée ?", "Évaluer les mesures de prévention et d'enquête.", "reponse de l employeur")
    add(QuestionPriority.USEFUL, "Des mesures défavorables ont-elles suivi le signalement ou le mandat ?", "Rechercher des représailles possibles.", "apres le signalement")
    if "appraisal" not in known_types:
        add(QuestionPriority.USEFUL, "Comment les évaluations ont-elles évolué avant et après les faits ?", "Comparer la trajectoire professionnelle.")
    if "career_history" not in known_types:
        add(QuestionPriority.COMPLEMENTARY, "L'historique de carrière, de formation et de classification est-il disponible ?", "Vérifier les évolutions dans le temps.")
    add(QuestionPriority.COMPLEMENTARY, "Le CSE, le référent compétent ou le service de prévention ont-ils été alertés ?", "Identifier les démarches internes déjà engagées.")
    return tuple(questions)
