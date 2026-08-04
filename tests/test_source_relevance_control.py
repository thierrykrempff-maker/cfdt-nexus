from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "nexus-local-interface"
sys.path.insert(0, str(APP_DIR))

from historical_cases import get_historical_case  # noqa: E402
from SYNDICAL_REASONING_ENGINE import (  # noqa: E402
    analyze_source_to_facts,
    build_case_factual_core,
    source_topic_relevance,
)


def _source(title: str, article: str, excerpt: str, source_id: str) -> dict[str, object]:
    return {
        "origin": "bible_accords",
        "source_layer": "accord_entreprise",
        "document": title,
        "article": article,
        "excerpt": excerpt,
        "official_id": source_id,
    }


def test_ppe_case_rejects_cse_governance_and_keeps_actual_ppe_clause() -> None:
    core = build_case_factual_core(
        "Le salarié n'a pas porté les EPI car la visière et les gants étaient indisponibles.",
        "QUESTION_SALARIE",
    )
    report = analyze_source_to_facts(
        core,
        (
            _source(
                "Accord sur la mise en place du CSE",
                "Article 5 - Périodicité des réunions du CSE",
                "La CSSCT contribue à l'analyse des risques professionnels.",
                "CSE-ARTICLE-5",
            ),
            _source(
                "Règlement intérieur",
                "Article 4 - EPI",
                "Les équipements de protection individuelle adaptés sont fournis et doivent être portés.",
                "RI-ARTICLE-4",
            ),
        ),
    )

    assert [item.source_title for item in report.applicable_sources] == [
        "Règlement intérieur"
    ]
    assert report.rejected_sources == (
        (
            "Accord sur la mise en place du CSE",
            "source générique ou hors sujet pour le fait principal",
        ),
    )


def test_generic_prevention_vocabulary_is_not_enough_for_ppe_evidence() -> None:
    relevant, reason = source_topic_relevance(
        "PPE_AVAILABILITY_OR_SUITABILITY",
        source_title="Convention collective de la chimie",
        source_reference="Prévention générale",
        source_excerpt="L'employeur améliore les conditions de travail et évite les risques professionnels.",
    )

    assert relevant is False
    assert "concept distinctif" in str(reason)


def test_badging_case_rejects_an_unrelated_shift_schedule_clause() -> None:
    relevant, reason = source_topic_relevance(
        "BREAKS_AND_BADGE_CONTROL",
        source_title="Avenant à l'accord 35 heures 5x8",
        source_reference="Temps annuel de travail",
        source_excerpt="Le cycle prévoit 190 postes et treize jours fériés.",
    )

    assert relevant is False
    assert "concept distinctif" in str(reason)


def test_insulting_email_case_rejects_an_unrelated_harassment_clause() -> None:
    relevant, reason = source_topic_relevance(
        "INSULTING_EMAILS",
        source_title="Règlement intérieur",
        source_reference="Harcèlement sexuel",
        source_excerpt=(
            "Aucun salarié ne peut être sanctionné pour avoir subi des faits "
            "de harcèlement sexuel ou certains propos non répétés."
        ),
    )

    assert relevant is False
    assert "concept distinctif" in str(reason)


def test_historical_ppe_presentation_contains_only_the_actual_ppe_rule() -> None:
    detail = get_historical_case("REAL-07")
    summary = detail["public_summary"]
    case_file = detail["union_case_file"]
    serialized = str(detail)

    assert [item["title"] for item in case_file["determinant_sources"]] == [
        "INEOS Sarralbe — Règlement intérieur"
    ]
    source = case_file["determinant_sources"][0]
    assert "Page 2" in source["reference"]
    assert "Art. 4" in source["reference"]
    assert "équipements de protection individuelle" in source["excerpt"]
    assert [item["source"] for item in summary["rule_to_facts"]] == [
        "INEOS Sarralbe — Règlement intérieur.pdf"
    ]
    assert "Périodicité des réunions" not in serialized
    assert "mise en place du CSE" not in serialized
    assert "ccnic_septembre2013.pdf" not in serialized


def test_historical_badging_and_email_cases_drop_keyword_only_documents() -> None:
    badge = get_historical_case("REAL-02")
    email = get_historical_case("REAL-01")

    badge_titles = [
        item["title"] for item in badge["union_case_file"]["determinant_sources"]
    ]
    email_titles = [
        item["title"] for item in email["union_case_file"]["determinant_sources"]
    ]
    assert badge_titles == [
        "INEOS Sarralbe — Règlement intérieur, horaires et pauses",
        "Légifrance — Code du travail",
    ]
    assert all("Avenant" not in title for title in badge_titles)
    assert email_titles == [
        "INEOS Sarralbe — Règlement intérieur, procédure disciplinaire",
        "Légifrance — Code du travail",
    ]
    assert all("Avenant" not in title for title in email_titles)


def test_cse_governance_source_remains_eligible_for_an_actual_cse_issue() -> None:
    relevant, reason = source_topic_relevance(
        "CSE_MEETING_REST_TIME",
        source_title="Accord sur la mise en place du CSE",
        source_reference="Article 5 - Périodicité des réunions",
        source_excerpt="Le temps passé en réunion du CSE est traité comme temps de travail.",
    )

    assert relevant is True
    assert reason is None


def test_unspecified_disciplinary_case_rejects_an_arbitrary_harassment_clause() -> None:
    relevant, reason = source_topic_relevance(
        "DISCIPLINARY_CASE_UNSPECIFIED",
        source_title="Règlement intérieur",
        source_reference="Harcèlement moral",
        source_excerpt=(
            "Tout salarié ayant procédé à des agissements de harcèlement moral "
            "est passible d'une sanction disciplinaire."
        ),
    )

    assert relevant is False
    assert "garantie procédurale" in str(reason)


def test_unspecified_disciplinary_case_keeps_neutral_procedural_guarantees() -> None:
    relevant, reason = source_topic_relevance(
        "DISCIPLINARY_CASE_UNSPECIFIED",
        source_title="Code du travail",
        source_reference="Article L1332-2",
        source_excerpt=(
            "Lorsque l'employeur envisage une sanction, il convoque le salarié "
            "à un entretien préalable et lui précise l'objet de la convocation."
        ),
    )

    assert relevant is True
    assert reason is None
