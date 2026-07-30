from NEXUS_RUNTIME_INTEGRATION import (
    PublicEvidenceDecision,
    sanitize_public_evidence_text,
)


def test_health_only_passage_is_rejected():
    result = sanitize_public_evidence_text(
        "Le salarié suit un traitement médical après un diagnostic individuel."
    )
    assert result.decision is PublicEvidenceDecision.REJECTED
    assert result.text is None
