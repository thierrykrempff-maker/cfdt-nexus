from __future__ import annotations

import pytest

from NEXUS_FINAL_ASSISTANT import AssistantRequest, NexusFinalAssistant
from NEXUS_FINAL_ASSISTANT.privacy import PrivacyGate
from tools.run_nexus_controlled_validation import execute_case, load_cases


def test_engine_exception_is_isolated_and_partial_response_is_kept() -> None:
    case = next(item for item in load_cases() if item.get("failure_engine"))
    result = execute_case(case)
    assert result["acceptable"] is True
    assert result["fallback"] is True
    assert result["engines_failed"] == ["cse_memory"]
    assert "SYNTHETIC_ENGINE_FAILURE" not in repr(result)


@pytest.mark.parametrize(
    "engine",
    ["syndical_reasoning", "cse_memory", "expert_paie_v2", "documentary"],
)
def test_each_optional_engine_can_fail_without_global_crash(engine: str) -> None:
    case = dict(load_cases()[0])
    case["failure_engine"] = engine
    case["allowed_engines"] = [engine]
    result = execute_case(case)
    assert result["mode"] == "FINAL_ASSISTANT"
    assert result["assistant"]["trace"]["fallback_used"] is True
    assert "traceback" not in repr(result).casefold()


def test_malformed_engine_output_is_safely_normalized() -> None:
    assistant = NexusFinalAssistant({"syndical_reasoning": lambda _: {"unexpected": True}})
    response = assistant.analyze(
        AssistantRequest(
            "Une sanction disciplinaire est évoquée.",
            allowed_engines=("syndical_reasoning",),
        )
    )
    assert response.trace.engines_failed == ()
    assert response.engine_results[0].available is True
    assert response.confidence.value in {"LOW", "MEDIUM"}


def test_logical_timeout_is_isolated_as_engine_failure() -> None:
    def timeout(_: AssistantRequest) -> dict[str, object]:
        raise TimeoutError("SYNTHETIC_LOGICAL_TIMEOUT")

    response = NexusFinalAssistant({"syndical_reasoning": timeout}).analyze(
        AssistantRequest(
            "Une sanction disciplinaire doit être analysée.",
            allowed_engines=("syndical_reasoning",),
        )
    )
    assert response.trace.fallback_used is True
    assert response.trace.engines_failed == ("syndical_reasoning",)
    assert "SYNTHETIC_LOGICAL_TIMEOUT" not in repr(response.to_dict())


def test_engine_contradiction_is_exposed_with_prudent_resolution() -> None:
    def certain(_: AssistantRequest) -> dict[str, object]:
        return {
            "mode": "SUCCEEDED",
            "analysis": {"findings": ["Le résultat est certain."]},
        }

    def cautious(_: AssistantRequest) -> dict[str, object]:
        return {
            "mode": "SUCCEEDED",
            "analysis": {"findings": ["La qualification reste à vérifier."]},
        }

    response = NexusFinalAssistant(
        {"syndical_reasoning": certain, "documentary": cautious}
    ).analyze(
        AssistantRequest(
            "Un document et un accord concernent une sanction disciplinaire.",
            allowed_engines=("syndical_reasoning", "documentary"),
        )
    )
    assert response.conflicts
    assert all("prudente" in conflict.resolution.casefold() for conflict in response.conflicts)


def test_sensitive_identifier_blocks_before_engine_execution() -> None:
    called = []
    assistant = NexusFinalAssistant(
        {"syndical_reasoning": lambda _: called.append(True) or {"mode": "SUCCEEDED"}}
    )
    response = assistant.analyze(
        AssistantRequest(
            "Sanction synthétique pour le numéro 1999999999999.",
            allowed_engines=("syndical_reasoning",),
        )
    )
    assert response.privacy.value == "BLOCKED"
    assert called == []
    assert "1999999999999" not in repr(response.to_dict())


@pytest.mark.parametrize(
    "synthetic_value",
    [
        "nom complet: Personne Fictive",
        "adresse: 1 rue Synthétique",
        "synthetic.user@example.invalid",
        "06 12 34 56 78",
        "matricule: SYNTH-001",
        "identifiant Kelio: K-SYNTH",
        "identifiant Nibelis: N-SYNTH",
        "salaire: 1234 euros",
        "diagnostic: diagnostic fictif",
        "RIB: RIB-SYNTHETIQUE",
        "contenu du PV: texte fictif réservé",
        "sanction disciplinaire: motif fictif réservé",
    ],
)
def test_dedicated_synthetic_sensitive_values_are_anonymized(
    synthetic_value: str,
) -> None:
    assessment = PrivacyGate().assess(
        AssistantRequest(f"Test de confidentialité synthétique ; {synthetic_value}")
    )
    assert assessment.decision.value == "ANONYMIZE_REQUIRED"
    assert synthetic_value.casefold() not in assessment.sanitized_question.casefold()
    assert "<redacted>" in assessment.sanitized_question


@pytest.mark.parametrize(
    "synthetic_value",
    [
        "1999999999999",
        "FR7612345678901234567890123",
    ],
)
def test_dedicated_synthetic_strong_identifiers_are_blocked(
    synthetic_value: str,
) -> None:
    assessment = PrivacyGate().assess(
        AssistantRequest(f"Test synthétique {synthetic_value}")
    )
    assert assessment.decision.value == "BLOCKED"
    assert synthetic_value not in assessment.sanitized_question
