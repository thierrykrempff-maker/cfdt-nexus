from __future__ import annotations

import json

from NEXUS_RUNTIME_INTEGRATION import build_final_response, sanitize_public_payload


def internal_answer(*, suspended: bool = False) -> dict:
    ambiguities = ["Nature exacte de la règle à identifier"] if suspended else []
    return {
        "query": "La direction envisage une sanction après un fait contesté.",
        "confidence": "MEDIUM",
        "route": {
            "domains": ["disciplinaire"],
            "analysis_suspended": suspended,
        },
        "case_factual_core": {
            "primary_event": "Une sanction est envisagée après un fait contesté.",
            "primary_grievance_or_decision": "Sanction envisagée",
            "employee_position": "Le salarié reconnaît un échange mais conteste sa portée.",
            "employer_position": "Le grief exact doit être demandé à la direction.",
            "facts_certain": ["Une convocation a été reçue.", "Une convocation a été reçue."],
            "facts_admitted": ["Un échange est reconnu."],
            "facts_disputed": ["La qualification de faute grave est contestée."],
            "facts_missing": ["Le contenu exact de l'échange", "La preuve complète"],
            "legal_ambiguities": ambiguities,
            "blocking_ambiguities": ambiguities,
            "forbidden_inferences": ["Ne pas présenter une allégation comme prouvée."],
            "sanction_or_measure_considered": "Sanction disciplinaire",
        },
        "actionable_preparation": {
            "questions_for_employee": [
                {
                    "question": "Que reconnaissez-vous exactement ?",
                    "priority": "BLOCKING",
                    "purpose": "Fixer la position du salarié.",
                },
                {
                    "question": "Que reconnaissez-vous exactement ?",
                    "priority": "BLOCKING",
                    "purpose": "Doublon à supprimer.",
                },
            ],
            "questions_for_employer": [
                {
                    "question": "Quel grief exact retenez-vous ?",
                    "priority": "HIGH",
                    "purpose": "Délimiter le grief.",
                }
            ],
            "documents_to_request": [
                {
                    "document": "Convocation et pièces complètes",
                    "priority": "BLOCKING",
                    "purpose": "Contrôler la procédure et la preuve.",
                }
            ],
        },
        "syndical_position": {
            "employee_strength": "La preuve complète reste à contrôler.",
            "employee_weakness": "Un échange est reconnu.",
            "point_to_challenge": "Contester toute qualification dépassant les faits établis.",
            "point_to_negotiate": "Rechercher une mesure proportionnée.",
            "do_not_say": "Ne pas annoncer que le dossier est gagné.",
        },
        "short_answer": "La position reste provisoire jusqu'au contrôle de la preuve.",
        "applicable_sources": [
            {
                "source_provider": "Légifrance",
                "source_title": "Code du travail",
                "legal_nature": "STATUTE",
                "retrieval_status": "RETRIEVED",
                "applicability_status": "APPLICABLE",
            }
        ],
        "rule_to_facts_analysis": [
            {
                "issue": "Procédure disciplinaire",
                "source_reference": "Légifrance — Code du travail — L1332-2",
                "facts_matching": ["Une convocation a été reçue."],
                "facts_missing": ["Le motif exact"],
                "provisional_conclusion": "À VÉRIFIER",
                "next_action": "Comparer la convocation au texte applicable.",
                "confidence": "MEDIUM",
            }
        ],
    }


def test_summary_has_at_most_twelve_non_empty_sections_and_bounded_items() -> None:
    result = build_final_response(internal_answer())
    summary = result["public_summary"]

    assert len(summary["sections"]) <= 12
    assert len(summary["situation"]) <= 6
    assert len(summary["syndical_position"]) <= 4
    assert len(summary["strengths"]) <= 3
    assert len(summary["weaknesses"]) <= 3
    assert len(summary["priority_questions"]) <= 10
    assert len(summary["documents"]) <= 5
    assert len(summary["rule_to_facts"]) <= 3
    assert len(summary["sources"]) <= 5
    assert all(section["items"] for section in summary["sections"])


def test_summary_deduplicates_questions_and_keeps_operational_context() -> None:
    summary = build_final_response(internal_answer())["public_summary"]

    questions = summary["priority_questions"]
    assert [item["question"] for item in questions].count(
        "Que reconnaissez-vous exactement ?"
    ) == 1
    assert all({"target", "question", "reason", "priority"} <= set(item) for item in questions)
    assert summary["documents"][0]["utility"]
    assert summary["sources"][0]["provider"] == "Légifrance"


def test_suspended_analysis_is_short_and_explicit() -> None:
    summary = build_final_response(internal_answer(suspended=True))["public_summary"]

    assert summary["analysis_suspended"] is True
    assert summary["urgency"] == "INFORMATION INSUFFISANTE"
    assert len(json.dumps(summary, ensure_ascii=False).encode("utf-8")) < 25_000


def test_suspended_public_payload_avoids_repeating_the_full_query() -> None:
    payload = sanitize_public_payload(
        {"ok": True, "answer": internal_answer(suspended=True)}
    )

    assert "query" not in payload["answer"]
    assert payload["public_summary"]["priority_questions"]
    assert payload["public_summary"]["documents"]
    assert payload["analysis_report"]["sections"]
    assert all(
        len(section["items"]) <= 1
        for section in payload["analysis_report"]["sections"]
    )


def test_public_boundary_keeps_detail_but_exports_summary_only() -> None:
    payload = sanitize_public_payload({"ok": True, "answer": internal_answer()})
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    assert payload["public_summary"]
    assert payload["detailed_analysis"]["factual_core"]
    assert payload["analysis_report"]["detail_available"] is True
    assert payload["analysis_report"]["export_scope"] == "PUBLIC_SUMMARY_ONLY"
    assert "Faits détaillés" not in payload["analysis_report"]["markdown"]
    assert len(encoded) < 30_000


def test_internal_answer_is_not_mutated_or_replaced() -> None:
    answer = internal_answer()
    before = json.dumps(answer, ensure_ascii=False, sort_keys=True)

    build_final_response(answer)

    assert json.dumps(answer, ensure_ascii=False, sort_keys=True) == before
    assert answer["rule_to_facts_analysis"][0]["facts_missing"] == ["Le motif exact"]
