from NEXUS_RUNTIME_INTEGRATION import sanitize_public_evidence_payload


def test_context_before_and_after_are_both_sanitized():
    payload = sanitize_public_evidence_payload(
        {
            "source_type": "CSE_CSSCT_MINUTES",
            "context_before": "Une grossesse individuelle est mentionnée.",
            "excerpt": "Le plan de prévention doit être revu.",
            "context_after": "Un traitement médicamenteux est détaillé.",
        }
    )
    assert "grossesse" not in str(payload).casefold()
    assert "médicament" not in str(payload).casefold()
    assert "prévention" in str(payload)
