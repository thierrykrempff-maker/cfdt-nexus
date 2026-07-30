from NEXUS_RUNTIME_INTEGRATION import sanitize_public_evidence_text


def test_generic_replacement_can_preserve_only_needed_health_context():
    result = sanitize_public_evidence_text(
        "Une restriction médicale individuelle est détaillée.",
        preserve_generic_health_context=True,
    )
    assert result.text == (
        "Des restrictions médicales individuelles sont mentionnées sans détail "
        "identifiable."
    )
