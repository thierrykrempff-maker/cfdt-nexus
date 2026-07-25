from __future__ import annotations

from NEXUS_FINAL_ASSISTANT import AssistantRequest, Domain, NexusFinalAssistant


def runner(name, calls, *, fail=False):
    def run(request):
        calls.append(name)
        if fail:
            raise RuntimeError("synthetic failure")
        return {
            "mode": "SUCCEEDED",
            "analysis": {
                "findings": [f"Qualification prudente {name}"],
                "missing_information": ["Période exacte ?"],
                "recommendations": ["Conserver les pièces"],
            },
        }
    return run


def test_orchestrator_calls_only_selected_engines_once_in_stable_order():
    calls = []
    assistant = NexusFinalAssistant(
        {
            "syndical_reasoning": runner("syndical_reasoning", calls),
            "expert_paie_v2": runner("expert_paie_v2", calls),
            "cse_memory": runner("cse_memory", calls),
            "documentary": runner("documentary", calls),
        }
    )
    result = assistant.analyze(
        AssistantRequest("Anomalie de paie collective avec heures supplémentaires")
    )
    assert calls == list(result.trace.engines_called)
    assert len(calls) == len(set(calls))
    assert len(calls) <= 4


def test_one_engine_failure_keeps_partial_results():
    calls = []
    assistant = NexusFinalAssistant(
        {
            "syndical_reasoning": runner("syndical_reasoning", calls),
            "expert_paie_v2": runner("expert_paie_v2", calls, fail=True),
        }
    )
    result = assistant.analyze(
        AssistantRequest("Bulletin avec heures supplémentaires non payées")
    )
    assert result.trace.fallback_used
    assert "expert_paie_v2" in result.trace.engines_failed
    assert any(item.available for item in result.engine_results)


def test_missing_runner_is_fail_safe():
    result = NexusFinalAssistant({}).analyze(AssistantRequest("Sanction disciplinaire"))
    assert result.trace.fallback_used
    assert result.confidence.value == "LOW"


def test_results_are_immutable():
    result = NexusFinalAssistant(
        {"syndical_reasoning": lambda _: {"mode": "SUCCEEDED"}}
    ).analyze(AssistantRequest("Sanction disciplinaire"))
    try:
        result.confidence = "HIGH"
    except (AttributeError, TypeError):
        pass
    else:
        raise AssertionError("Final result must be immutable")


def test_no_cross_request_contamination():
    assistant = NexusFinalAssistant(
        {"syndical_reasoning": lambda _: {"mode": "SUCCEEDED"}}
    )
    first = assistant.analyze(AssistantRequest("Sanction disciplinaire"))
    second = assistant.analyze(AssistantRequest("Arrêt maladie"))
    assert first.plan.primary_domain is Domain.DISCIPLINE
    assert second.plan.primary_domain is Domain.HEALTH
