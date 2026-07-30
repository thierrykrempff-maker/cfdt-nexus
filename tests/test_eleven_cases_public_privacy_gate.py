from NEXUS_RUNTIME_INTEGRATION import sanitize_public_evidence_payload


def test_public_privacy_gate_covers_all_evidence_projection_shapes():
    payload = sanitize_public_evidence_payload(
        {
            "public_summary": {
                "cse_context": [{"excerpt": "Un diagnostic individuel est détaillé."}],
                "source_extractions": [{"excerpt": "Un traitement est mentionné."}],
                "rule_to_facts": [{"rule": "Une grossesse est signalée."}],
            },
            "detailed_analysis": {
                "retrieval_evidence": [
                    {"raw_excerpt": "Un arrêt maladie individuel est décrit."}
                ]
            },
        }
    )
    text = str(payload).casefold()
    for marker in ("diagnostic", "traitement", "grossesse", "arrêt maladie"):
        assert marker not in text
