"""Prioritized questions that never request a diagnosis."""

from __future__ import annotations

from .health_absence_models import HealthQuestion, QuestionPriority
from .models import SyndicalCaseInput


def build_health_questions(case: SyndicalCaseInput, *, urgent: bool) -> tuple[HealthQuestion, ...]:
    known = {item.document_type for item in case.available_pieces}
    result = []

    def add(priority: QuestionPriority, question: str, purpose: str, document: str | None = None) -> None:
        if document and document in known:
            return
        result.append(HealthQuestion(priority, question, purpose))

    if urgent:
        add(QuestionPriority.CRITICAL, "Existe-t-il un danger immédiat, une urgence humaine ou une absence totale de revenu ?", "Prioriser l'orientation compétente.")
    add(QuestionPriority.CRITICAL, "Quelle est la nature administrative exacte de l'absence et quelles sont ses dates ?", "Structurer la chronologie sans détail médical.")
    add(QuestionPriority.PRIORITY, "Existe-t-il un arrêt ou une prolongation transmis à l'employeur et à la CPAM ?", "Vérifier les transmissions.", "sick_leave_notice")
    add(QuestionPriority.PRIORITY, "Une déclaration d'accident et une décision CPAM existent-elles ?", "Distinguer déclaration et reconnaissance.", "cpam_decision")
    add(QuestionPriority.PRIORITY, "Les IJSS sont-elles indiquées sur un décompte ?", "Identifier le traitement administratif.", "daily_allowance_statement")
    add(QuestionPriority.PRIORITY, "Le maintien, la subrogation ou une régularisation apparaissent-ils sur un bulletin ?", "Repérer une anomalie apparente sans calcul.", "payslip")
    add(QuestionPriority.PRIORITY, "Quel accord, convention ou régime administratif est déclaré applicable ?", "Identifier les sources à vérifier sans présumer du droit.")
    add(QuestionPriority.USEFUL, "Une visite de préreprise ou de reprise a-t-elle eu lieu ?", "Vérifier l'organisation de la reprise.", "occupational_health_opinion")
    add(QuestionPriority.USEFUL, "Existe-t-il un avis minimal ou des restrictions déclarées, sans détail médical ?", "Identifier l'acteur et la procédure compétents.")
    add(QuestionPriority.USEFUL, "Un aménagement ou des postes de reclassement ont-ils été proposés par écrit ?", "Examiner les démarches employeur.", "redeployment_proposal")
    add(QuestionPriority.USEFUL, "Une notice et un dossier de prévoyance sont-ils disponibles ?", "Vérifier une garantie potentielle.", "provident_notice")
    add(QuestionPriority.COMPLEMENTARY, "Les congés, l'ancienneté ou les primes ont-ils été modifiés ?", "Repérer des incidences potentielles.")
    add(QuestionPriority.COMPLEMENTARY, "Une procédure disciplinaire ou une rupture est-elle envisagée ?", "Articuler R1B et les urgences contractuelles.")
    return tuple(result)
