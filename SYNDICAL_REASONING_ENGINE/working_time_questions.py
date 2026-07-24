"""Four-level prioritized working-time questions."""

from __future__ import annotations

from .models import SyndicalCaseInput
from .working_time_models import QuestionPriority, WorkingTimeQuestion, WorkingTimeSituation


PRIORITY_ORDER = {
    QuestionPriority.CRITICAL: 0,
    QuestionPriority.PRIORITY: 1,
    QuestionPriority.USEFUL: 2,
    QuestionPriority.COMPLEMENTARY: 3,
}


def build_working_time_questions(
    case: SyndicalCaseInput,
    situations: tuple[WorkingTimeSituation, ...],
) -> tuple[WorkingTimeQuestion, ...]:
    present = {item.document_type for item in case.available_pieces}
    selected = set(situations)
    questions: list[WorkingTimeQuestion] = []

    def add(level: QuestionPriority, question: str, purpose: str) -> None:
        questions.append(WorkingTimeQuestion(level, question, purpose))

    if "employment_contract" not in present:
        add(QuestionPriority.CRITICAL, "Quel est l'horaire contractuel ?", "Identifier le cadre contractuel déclaré.")
    add(QuestionPriority.CRITICAL, "Quel est le régime de travail réellement appliqué ?", "Distinguer horaire, cycle, annualisation et travail posté.")
    if "official_schedule" not in present:
        add(QuestionPriority.CRITICAL, "Existe-t-il un cycle ou un planning officiel ?", "Établir l'organisation théorique.")
    add(QuestionPriority.CRITICAL, "Quelles heures ont réellement été réalisées ?", "Comparer le prévu, le déclaré et le constaté.")
    if "timeclock" not in present:
        add(QuestionPriority.PRIORITY, "Existe-t-il des badgeages pour la période concernée ?", "Obtenir un indice technique daté.")
    if selected.intersection({WorkingTimeSituation.BREAK, WorkingTimeSituation.INTERRUPTED_BREAK}):
        add(QuestionPriority.CRITICAL, "La pause a-t-elle été interrompue ?", "Identifier les interventions réelles.")
        add(QuestionPriority.CRITICAL, "Le salarié pouvait-il vaquer librement à ses occupations ?", "Apprécier la disponibilité exigée.")
    if selected.intersection({WorkingTimeSituation.ON_CALL, WorkingTimeSituation.ON_CALL_INTERVENTION}):
        add(QuestionPriority.CRITICAL, "Une astreinte était-elle planifiée ?", "Distinguer astreinte et intervention.")
        add(QuestionPriority.CRITICAL, "Une intervention a-t-elle effectivement eu lieu ?", "Qualifier le temps d'intervention.")
        add(QuestionPriority.PRIORITY, "La durée de l'intervention et son trajet sont-ils connus ?", "Reconstituer la chronologie sans calcul.")
    if selected.intersection({WorkingTimeSituation.DAILY_REST, WorkingTimeSituation.RECALL_DURING_REST}):
        add(QuestionPriority.CRITICAL, "Le repos quotidien suivant a-t-il été respecté ?", "Identifier un risque urgent à vérifier.")
    if selected.intersection({WorkingTimeSituation.SHIFT_WORK, WorkingTimeSituation.FIVE_SHIFT}):
        add(QuestionPriority.PRIORITY, "Le salarié travaille-t-il en poste ou en organisation 5x8 ?", "Identifier le cycle réel.")
    if "kelio_statement" not in present:
        add(QuestionPriority.PRIORITY, "Les heures et événements sont-ils présents dans Kelio ?", "Comparer le compteur à la chronologie.")
    if "payslip" not in present:
        add(QuestionPriority.PRIORITY, "Les événements apparaissent-ils sur le bulletin Nibelis ?", "Rechercher une incidence potentielle, sans calcul.")
    add(QuestionPriority.PRIORITY, "Une prime, une majoration ou une contrepartie semble-t-elle absente ?", "Qualifier uniquement une anomalie apparente.")
    add(QuestionPriority.USEFUL, "Quel accord INEOS encadre la situation ?", "Identifier la source conventionnelle applicable.")
    if "amendment" not in present:
        add(QuestionPriority.USEFUL, "Existe-t-il un avenant ou une note de service ?", "Identifier une règle contractuelle ou organisationnelle.")
    add(QuestionPriority.USEFUL, "Le problème est-il ponctuel ou récurrent ?", "Distinguer incident et pratique.")
    add(QuestionPriority.COMPLEMENTARY, "Plusieurs salariés sont-ils concernés ?", "Identifier une dimension collective.")
    add(QuestionPriority.COMPLEMENTARY, "Le CSE a-t-il été informé ou consulté ?", "Vérifier l'articulation collective.")
    unique = {(item.question, item.purpose): item for item in questions}
    return tuple(
        sorted(
            unique.values(),
            key=lambda item: (PRIORITY_ORDER[item.priority], item.question),
        )
    )
