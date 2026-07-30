from NEXUS_RUNTIME_INTEGRATION import sanitize_public_evidence_text


def test_medical_sentence_is_removed_while_collective_prevention_is_kept():
    result = sanitize_public_evidence_text(
        "Deux personnes présentent des symptômes gastriques avec du sang. "
        "L’adéquation des EPI doit être vérifiée et le plan de prévention revu."
    )
    assert "sang" not in result.text.casefold()
    assert "sympt" not in result.text.casefold()
    assert "EPI" in result.text
    assert "prévention" in result.text
