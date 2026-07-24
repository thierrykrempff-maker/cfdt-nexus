"""Deterministic metadata-only document comparisons."""

from __future__ import annotations

from .models import ConfidenceLevel, SyndicalCaseInput
from .working_time_models import DocumentComparison


COMPARISON_SPECS = (
    ("schedule_timeclock", "official_schedule", "timeclock", ("annualisation ou modulation", "validation hiérarchique", "correction de pointage")),
    ("schedule_kelio", "official_schedule", "kelio_statement", ("période de clôture", "paramétrage du cycle", "événement non validé")),
    ("on_call_intervention", "on_call_record", "intervention_sheet", ("astreinte sans intervention", "feuille non transmise", "décalage d'enregistrement")),
    ("intervention_rest", "intervention_sheet", "rest_record", ("repos restauré ultérieurement", "horaire incomplet", "changement de poste")),
    ("event_nibelis", "event_record", "payslip", ("décalage de paie", "période de clôture", "régularisation ultérieure", "erreur de saisie", "paramétrage", "événement non validé")),
    ("agreement_observed", "company_agreement", "observed_treatment", ("accord non applicable à la période", "dispositif équivalent", "donnée observée incomplète")),
    ("planned_actual_cycle", "work_cycle", "actual_cycle", ("remplacement ponctuel", "changement temporaire", "planning incomplet")),
    ("worked_compensated_days", "worked_days", "compensation_record", ("compensation différée", "repos affecté à une autre période", "validation en attente")),
    ("leave_counter", "leave_record", "leave_counter", ("décalage de mise à jour", "demande non validée", "période différente")),
)


def compare_documents(case: SyndicalCaseInput) -> tuple[DocumentComparison, ...]:
    present = {item.document_type for item in case.available_pieces}
    text = case.question.lower()
    discrepancy_signal = any(marker in text for marker in ("écart", "absent", "non retrouvé", "manquant", "différent"))
    comparisons = []
    for code, left, right, alternatives in COMPARISON_SPECS:
        left_present = _is_present(left, present)
        right_present = _is_present(right, present)
        available = tuple(
            item
            for item, is_available in ((left, left_present), (right, right_present))
            if is_available
        )
        if not available and code not in _relevant_codes(text):
            continue
        both = left_present and right_present
        comparisons.append(
            DocumentComparison(
                code,
                left,
                right,
                ("deux pièces disponibles pour rapprochement",) if both else (),
                ("incohérence apparente à vérifier",) if both and discrepancy_signal else (),
                alternatives,
                tuple(
                    item
                    for item, is_available in ((left, left_present), (right, right_present))
                    if not is_available
                ),
                ConfidenceLevel.MODERATE if both else ConfidenceLevel.LOW,
                "traitement potentiellement incomplet" if discrepancy_signal else "données insuffisantes pour conclure",
            )
        )
    return tuple(comparisons)


def _is_present(document_type: str, present: set[str]) -> bool:
    aliases = {
        "event_record": {"event_record", "kelio_statement", "intervention_sheet"},
        "observed_treatment": {"observed_treatment", "payslip", "kelio_statement"},
        "actual_cycle": {"actual_cycle", "kelio_statement", "timeclock"},
    }
    return bool(aliases.get(document_type, {document_type}).intersection(present))


def _relevant_codes(text: str) -> set[str]:
    result = set()
    if "kelio" in text or "badge" in text or "heure supplémentaire" in text:
        result.update({"schedule_timeclock", "schedule_kelio"})
    if "astreinte" in text or "intervention" in text:
        result.update({"on_call_intervention", "intervention_rest"})
    if "nibelis" in text or "bulletin" in text or "prime" in text:
        result.add("event_nibelis")
    if "cycle" in text or "5x8" in text:
        result.add("planned_actual_cycle")
    if "congé" in text or "rtt" in text:
        result.add("leave_counter")
    return result
