from NEXUS_RUNTIME_INTEGRATION import sanitize_public_evidence_payload


def test_sensitive_summary_is_sanitized_recursively():
    payload = sanitize_public_evidence_payload(
        {
            "public_summary": {
                "source_extractions": [
                    {
                        "title": "CSSCT",
                        "summary": "Un diagnostic est évoqué. Les EPI doivent être adaptés.",
                    }
                ]
            }
        }
    )
    text = str(payload)
    assert "diagnostic" not in text.casefold()
    assert "EPI" in text
