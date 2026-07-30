from NEXUS_RUNTIME_INTEGRATION import build_final_response


def test_presentation_does_not_copy_questions_and_positions_into_strategy() -> None:
    answer = {
        "case_factual_core": {"primary_event": "Un changement est annoncé."},
        "actionable_preparation": {
            "questions_for_employee": [
                {
                    "question": "Quel horaire est annoncé ?",
                    "priority": "BLOCKING",
                    "purpose": "Identifier le changement.",
                }
            ]
        },
        "syndical_position": {
            "point_to_challenge": "Contester ce qui dépasse les faits.",
            "point_to_negotiate": "Négocier un aménagement.",
        },
        "working_position": "Négocier un aménagement.",
        "next_action": "Quel horaire est annoncé ?",
    }

    summary = build_final_response(answer)["public_summary"]
    strategy = summary.get("strategy", {})

    assert "Quel horaire est annoncé ?" not in strategy.get("before", [])
    assert "Contester ce qui dépasse les faits." not in strategy.get("during", [])
    assert "Négocier un aménagement." not in strategy.get("position", [])
    assert "Quel horaire est annoncé ?" not in summary.get("next_actions", [])
