from NEXUS_RUNTIME_INTEGRATION import build_final_response


def test_epi_context_keeps_prevention_and_removes_medical_detail():
    final = build_final_response(
        {
            "retrieval_public_evidence": [
                {
                    "source_type": "CSE_CSSCT_MINUTES",
                    "title": "CSSCT",
                    "reference": "page 2",
                    "excerpt": (
                        "Deux salariés présentent des symptômes gastriques avec du "
                        "sang. L’adéquation des EPI et le plan de prévention sont à revoir."
                    ),
                    "legal_value": "Contexte uniquement.",
                    "usable_in_public_response": True,
                }
            ]
        }
    )
    text = str(final)
    assert "sang" not in text.casefold()
    assert "gastr" not in text.casefold()
    assert "EPI" in text
    assert "prévention" in text
