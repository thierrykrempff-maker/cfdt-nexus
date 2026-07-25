"""Build one bounded, readable and non-decisional synthesis."""

from __future__ import annotations

from .models import AnalysisPlan, AssistantRequest, Conflict, NormalizedEngineResult, ResponseMode


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
        if plan.response_mode is ResponseMode.QUICK:
            qualifications = qualifications[:2]
            missing = missing[:3]
            strategies = strategies[:3]
        return {
            "understanding": facts[:4] or ("Situation déclarée à préciser.",),
            "qualifications": qualifications or ("Aucune qualification définitive sans vérification.",),
            "missing": missing,
            "sources_to_verify": plan.sources_to_search[:8],
            "employee_arguments": tuple(dict.fromkeys(item for result in results for item in result.employee_arguments)),
            "employer_arguments": tuple(dict.fromkeys(item for result in results for item in result.employer_arguments)),
            "risks_and_urgencies": tuple(dict.fromkeys((*risks, *(item for result in results for item in result.urgencies)))) or ("Urgence à apprécier selon les faits vérifiés.",),
            "action_plan": strategies or ("Rassembler les pièces et vérifier les sources prioritaires.",),
            "documents_or_actions": tuple(dict.fromkeys(item for result in results for item in result.possible_actions)) or ("Préparer une chronologie factuelle.",),
            "limits": tuple((*limits, *(conflict.explanation for conflict in conflicts))) or ("Analyse prudente fondée sur les seules informations disponibles.",),
        }
