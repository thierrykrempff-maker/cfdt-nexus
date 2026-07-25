"""Generate bounded drafts; never send or execute an action."""

from __future__ import annotations

from .models import ActionDraft, AnalysisPlan, AssistantRequest, NormalizedEngineResult


class ActionGenerator:
    def generate(
        self,
        request: AssistantRequest,
        plan: AnalysisPlan,
        results: tuple[NormalizedEngineResult, ...],
    ) -> tuple[ActionDraft, ...]:
        proposed = tuple(
            dict.fromkeys(action for result in results for action in result.possible_actions)
        )
        action_type = "demande_documents" if plan.missing_data else "fiche_synthese_syndicale"
        if "courrier" in request.expected_output.lower():
            action_type = "courrier_direction"
        elif plan.primary_domain.value.startswith("cse_"):
            action_type = "question_ordre_du_jour"
        requests = proposed[:3] or tuple(
            f"Vérifier : {item}" for item in plan.sources_to_search[:3]
        )
        return (
            ActionDraft(
                action_type,
                f"Suivi prudent — {plan.primary_domain.value}",
                (f"Domaine principal : {plan.primary_domain.value}",),
                tuple(fact.statement for fact in request.facts if fact.documented),
                tuple(fact.statement for fact in request.facts if not fact.documented),
                requests,
                None,
                request.available_documents,
                "Ne pas présenter les hypothèses comme des faits établis.",
            ),
        )
