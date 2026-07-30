from NEXUS_RUNTIME_INTEGRATION import sanitize_public_evidence_text


def test_identity_is_not_retained_with_health_information():
    result = sanitize_public_evidence_text(
        "Mme Exemple est en arrêt maladie après un diagnostic. "
        "Une mesure collective de prévention est discutée."
    )
    assert "Mme Exemple" not in (result.text or "")
    assert "arrêt maladie" not in (result.text or "")
    assert "prévention" in result.text
