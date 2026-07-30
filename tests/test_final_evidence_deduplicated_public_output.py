from NEXUS_RUNTIME_INTEGRATION import build_final_response


def test_same_pv_excerpt_is_displayed_only_once():
    excerpt = "La badgeuse est située à proximité du tourniquet."
    final = build_final_response(
        {
            "retrieval_public_evidence": [
                {
                    "source_type": "CSE_CSSCT_MINUTES",
                    "title": "CE 2017",
                    "reference": "page 1",
                    "excerpt": excerpt,
                    "legal_value": "Contexte uniquement.",
                    "usable_in_public_response": True,
                }
            ],
            "source_extraction": {
                "sources": [
                    {
                        "title": "CE 2017",
                        "reference": "page 1",
                        "excerpt": excerpt,
                        "link_to_facts": "Éclaire la pratique interne de badgeage.",
                    }
                ]
            },
            "rule_to_facts_analysis": [
                {
                    "source_reference": "CE 2017 page 1",
                    "rule_summary": excerpt,
                    "issue": "Finalité du badgeage",
                    "facts_matching": ["Badgeage au tourniquet"],
                    "provisional_conclusion": "INSUFFICIENT_INFORMATION",
                    "next_action": "Vérifier la finalité.",
                }
            ],
        }
    )
    assert str(final).count(excerpt) == 1
