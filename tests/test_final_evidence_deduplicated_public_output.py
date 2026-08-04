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
    assert final["public_summary"].get("rule_to_facts", []) == []
    assert final["public_summary"]["cse_context"][0]["title"] == "CE 2017"


def test_title_only_catalog_entry_is_not_presented_as_a_consulted_source():
    final = build_final_response(
        {
            "source_extraction": {
                "sources": [
                    {
                        "provider": "CARSAT",
                        "title": "Missions de la Carsat Alsace-Moselle",
                        "availability_status": "TITLE_ONLY",
                        "link_to_facts": "Prévention des risques professionnels.",
                    },
                    {
                        "provider": "INEOS Sarralbe",
                        "title": "Règlement intérieur",
                        "availability_status": "FOUND_VERSION_UNCERTAIN",
                        "excerpt": "Les équipements de protection individuelle doivent être portés.",
                        "link_to_facts": "Consigne EPI à vérifier.",
                    },
                ]
            }
        }
    )

    assert final["public_summary"]["sources"] == [
        {"provider": "INEOS Sarralbe", "title": "Règlement intérieur"}
    ]
    assert all(
        item.get("title") != "Missions de la Carsat Alsace-Moselle"
        for item in final["public_summary"].get("source_extractions", ())
    )
