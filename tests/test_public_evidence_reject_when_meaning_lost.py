from NEXUS_RUNTIME_INTEGRATION import (
    PublicEvidenceDecision,
    sanitize_public_evidence_text,
)


def test_passage_is_rejected_when_redaction_removes_all_meaning():
    result = sanitize_public_evidence_text("Diagnostic et traitement médicamenteux.")
    assert result.decision is PublicEvidenceDecision.REJECTED
    assert result.text is None
