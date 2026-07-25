from __future__ import annotations

import pytest

from NEXUS_FINAL_ASSISTANT import AssistantRequest, NexusFinalAssistant, PrivacyDecision


@pytest.mark.parametrize(
    "value",
    (
        "Mon email est personne@example.org",
        "Mon téléphone est 06 12 34 56 78",
        "Mon matricule: RH-9988",
        "Mon salaire: 2450 euros",
    ),
)
def test_sensitive_values_are_redacted(value):
    result = NexusFinalAssistant({}).analyze(AssistantRequest(value))
    assert result.privacy is PrivacyDecision.ANONYMIZE
    assert "<redacted>" in result.request.question
    assert value not in str(result.to_dict())


@pytest.mark.parametrize(
    "value",
    (
        "NIR 1800675123456",
        "IBAN FR7630006000011234567890189",
    ),
)
def test_strong_identifiers_block_publication(value):
    result = NexusFinalAssistant({}).analyze(AssistantRequest(value))
    assert result.privacy is PrivacyDecision.BLOCKED
    assert not result.engine_results


def test_technical_paths_and_identifiers_are_rejected_from_public_output():
    assistant = NexusFinalAssistant(
        {
            "syndical_reasoning": lambda _: {
                "mode": "SUCCEEDED",
                "analysis": {"findings": ["local_path C:\\secret\\file"]},
            }
        }
    )
    with pytest.raises(ValueError, match="PUBLIC_OUTPUT_PRIVACY_FAILED"):
        assistant.analyze(AssistantRequest("Sanction"))


def test_diagnostics_never_contain_original_sensitive_value():
    value = "personne@example.org"
    result = NexusFinalAssistant({}).analyze(AssistantRequest(value))
    assert value not in str(result.trace)
    assert value not in str(result.warnings)
