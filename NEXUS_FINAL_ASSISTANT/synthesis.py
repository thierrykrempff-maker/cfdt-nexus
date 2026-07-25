"""Build one bounded, readable and non-decisional synthesis."""

from __future__ import annotations

from .models import AnalysisPlan, AssistantRequest, Conflict, NormalizedEngineResult, ResponseMode
from .sources import merge_sources


class SynthesisEngine:
    def build(
        self,
        request: AssistantRequest,
        plan: AnalysisPlan,
        results: tuple[NormalizedEngineResult, ...],
        conflicts: tuple[Conflict, ...],
    ) -> dict[str, tuple[str, ...]]:
        facts = tuple(dict.fromkeys(fact.statement for fact in request.facts))
        qualifications = tuple(
            dict.fromkeys(item for result in results for item in result.possible_qualifications)
        )
        missing = tuple(dict.fromkeys((*plan.missing_data, *(item for result in results for item in result.missing_information))))
        risks = tuple(dict.fromkeys(item for result in results for item in result.risks))
        strategies = tuple(dict.fromkeys(item for result in results for item in result.strategies))
        limits = tuple(dict.fromkeys(item for result in results for item in result.limits))
        sources = merge_sources(
            tuple(source for result in results for source in result.sources)
        )
        primary_source = sources[:1]
        case_law = tuple(
            source
            for source in sources
            if source.source_type in {"case_law", "jurisprudence"}
        )
        cse_history = tuple(
            source
            for source in sources
            if source.source_type in {"cse_document", "cse_history"}
        )
        employee_arguments = tuple(
            dict.fromkeys(
                item for result in results for item in result.employee_arguments
            )
        )
        employer_arguments = tuple(
            dict.fromkeys(
                item for result in results for item in result.employer_arguments
            )
        )
        actions = tuple(
            dict.fromkeys(item for result in results for item in result.possible_actions)
        )
        if plan.response_mode is ResponseMode.QUICK:
            qualifications = qualifications[:2]
            missing = missing[:3]
            strategies = strategies[:3]
        return {
            "understanding": facts[:4] or ("Situation déclarée à préciser.",),
            "factual_answer": qualifications
            or (
                "Les informations disponibles permettent une première analyse, "
                "mais pas une conclusion juridique définitive.",
            ),
            "primary_source": tuple(
                (
                    f"{source.title}"
                    + (
                        f" — référence à vérifier : {source.document_to_verify}"
                        if source.document_to_verify
                        else ""
                    )
                )
                for source in primary_source
            )
            or (
                "Aucune source principale vérifiée n'a été retrouvée ; aucune règle n'est inventée.",
            ),
            "comparative_analysis": (
                (
                    "Comparer directement la règle principale aux faits déclarés, "
                    "à son champ d'application et aux exceptions possibles ; "
                    "les faits non documentés restent à confirmer."
                ),
            ),
            "comparable_case_law": tuple(
                (
                    f"{source.title}"
                    + (f" — {source.date}" if source.date else "")
                    + " — comparaison factuelle requise avant toute transposition."
                )
                for source in case_law
            )
            or (
                "Aucune jurisprudence comparable vérifiée n'a été retenue.",
            ),
            "cse_elements": tuple(
                f"{source.title} — élément de contexte ou de preuve, non règle juridique."
                for source in cse_history
            )
            or (
                "Aucun passage vérifié de procès-verbal du CSE n'a été retrouvé.",
            ),
            "employee_arguments": employee_arguments
            or ("Arguments du salarié à consolider à partir des faits et de la source principale.",),
            "employer_arguments": employer_arguments
            or ("Arguments possibles de l'employeur à demander et à vérifier loyalement.",),
            "solutions": strategies
            or ("Demander une explication écrite et constituer une chronologie factuelle.",),
            "expert_advice": (
                "Distinguer l'urgence immédiate, la stratégie individuelle et la stratégie collective ; "
                "préserver les preuves et ne pas présenter une hypothèse comme une certitude.",
            ),
            "qualifications": qualifications or ("Aucune qualification définitive sans vérification.",),
            "sources_to_verify": plan.sources_to_search[:8],
            "risks_and_urgencies": tuple(dict.fromkeys((*risks, *(item for result in results for item in result.urgencies)))) or ("Urgence à apprécier selon les faits vérifiés.",),
            "action_plan": strategies or ("Rassembler les pièces et vérifier les sources prioritaires.",),
            "documents_or_actions": actions or ("Préparer une chronologie factuelle.",),
            "documents_indispensable": tuple(
                item for item in missing if "document" in item.casefold()
            )
            or (
                "Aucun document n'est déclaré indispensable avant la première analyse.",
            ),
            "documents_useful": tuple(
                item for item in missing if "document" not in item.casefold()
            )
            or ("Les pièces utiles dépendent des points factuels restant à confirmer.",),
            "documents_not_required": (
                "Ne pas demander de pièce sans expliquer son utilité pour la question traitée.",
            ),
            "missing": missing,
            "limits": tuple((*limits, *(conflict.explanation for conflict in conflicts))) or ("Analyse prudente fondée sur les seules informations disponibles.",),
        }
