"""Prioritized questions for disciplinary cases."""

from __future__ import annotations

from .contract_change_models import PrioritizedQuestion
from .disciplinary_models import (
    DisciplinaryActCategory,
    DisciplinaryFactExtraction,
    DisciplinaryQualification,
    DisciplinaryQualificationCandidate,
)
from .models import SyndicalCaseInput


def build_disciplinary_questions(
    case: SyndicalCaseInput,
    candidates: tuple[DisciplinaryQualificationCandidate, ...],
    facts: DisciplinaryFactExtraction,
) -> tuple[PrioritizedQuestion, ...]:
    known_types = {item.document_type for item in case.available_pieces}
    qualifications = {item.qualification for item in candidates}
    questions: list[PrioritizedQuestion] = []

    def add(priority: int, question: str, purpose: str) -> None:
        questions.append(PrioritizedQuestion(priority, question, purpose))

    if (
        facts.act_category
        == DisciplinaryActCategory.INSULTING_OR_INAPPROPRIATE_BEHAVIOR
    ):
        for question, purpose in (
            ("Le salarié reconnaît-il être l'auteur ?", "Fixer sa position avant toute stratégie de défense."),
            ("Quelle était la phrase exacte ?", "Éviter de raisonner sur une reformulation imprécise."),
            ("Où était-elle inscrite ?", "Apprécier le contexte et les conséquences concrètes."),
            ("Était-elle visible par les collègues, l'encadrement ou le public ?", "Mesurer la diffusion réelle."),
            ("Une personne pouvait-elle raisonnablement se sentir visée ?", "Distinguer propos non adressé et injure dirigée."),
            ("La direction identifie-t-elle une victime précise ?", "Vérifier le grief exact et le risque accru."),
            ("Existe-t-il une photographie, une vidéo, un témoin ou un aveu ?", "Contrôler la preuve de l'acte et de son attribution."),
            ("L'inscription a-t-elle causé une dégradation ou seulement nécessité un nettoyage ?", "Distinguer propos fautif et dommage matériel."),
            ("A-t-elle été effacée rapidement ?", "Évaluer les conséquences et une éventuelle réparation."),
            ("Le salarié a-t-il présenté des excuses ou exprimé des regrets ?", "Préparer une reconnaissance mesurée si les faits sont admis."),
            ("S'agit-il d'un fait isolé ou répété ?", "Apprécier la gravité et la proportionnalité."),
            ("Existe-t-il des antécédents disciplinaires ?", "Vérifier un facteur aggravant ou atténuant."),
            ("Quelle sanction est envisagée ?", "Comparer la mesure aux faits réellement établis."),
            ("Quel événement précis explique la journée difficile ou l'ambiance dégradée ?", "Documenter le contexte sans justifier automatiquement le geste."),
            ("Le salarié avait-il déjà signalé ce contexte ?", "Vérifier les traces contemporaines et la connaissance de l'employeur."),
        ):
            add(1 if "preuve" in purpose or "position" in purpose else 2, question, purpose)

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
    if facts.act_category == DisciplinaryActCategory.TECHNICAL_ERROR:
        add(
            2,
            "Quelles consignes techniques, formations et habilitations encadraient réellement la manipulation ?",
            "Analyser le volet technique uniquement lorsqu'il est présent dans les faits.",
        )
    if DisciplinaryQualification.REFUSAL_CONTRACT_CHANGE in qualifications:
        add(2, "Quel changement contractuel a été proposé et le salarié l'a-t-il refusé explicitement ?", "Distinguer refus contractuel et insubordination alléguée.")
    add(3, "Quels accords INEOS et dispositions conventionnelles sont applicables ?", "Identifier les garanties conventionnelles.")
    add(3, "Existe-t-il une jurisprudence réellement comparable et à jour ?", "Éviter une analogie non vérifiée.")
    unique = {(item.question, item.purpose): item for item in questions}
    return tuple(sorted(unique.values(), key=lambda item: (item.priority, item.question)))
