from NEXUS_RUNTIME_INTEGRATION import build_final_response


def test_final_response_has_distinct_non_normative_cse_section():
    answer = {
        "case_factual_core": {
            "primary_event": "Changement d'horaires annoncé.",
            "employee_position": "Le salarié demande des explications.",
            "employer_position": "La direction invoque une réorganisation.",
        },
        "retrieval_public_evidence": [
            {
                "source_family": "CSE_MINUTES",
                "source_type": "CSE_CSSCT_MINUTES",
                "organization": "CSE",
                "passage_nature": "INFORMATION",
                "retrieval_status": "LOCAL_DOCUMENT",
                "title": "PV CSE du 12 mars 2024",
                "reference": "page 3",
                "date": "2024-03-12",
                "excerpt": "La direction annonce une étude sur les horaires.",
                "relevance_score": 91,
                "relevance_justification": "Le passage traite des horaires.",
                "limits": ["Ne prouve pas une consultation achevée."],
                "legal_value": "Ce passage ne constitue pas une norme juridique.",
                "usable_in_public_response": True,
            }
        ],
        "retrieval_propagation": {
            "received_count": 1,
            "linked_count": 1,
            "selected_count": 1,
            "rejected_count": 0,
        },
    }
    final = build_final_response(answer)
    context = final["public_summary"]["cse_context"][0]
    assert context["title"] == "PV CSE du 12 mars 2024"
    assert context["organization"] == "CSE"
    assert context["passage_nature"] == "INFORMATION"
    assert "ne constitue pas une norme" in context["legal_value"]
    assert any(
        section["id"] == "cse_context"
        for section in final["public_summary"]["sections"]
    )
