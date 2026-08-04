from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "nexus-local-interface"
sys.path.insert(0, str(APP_DIR))

from historical_cases import get_historical_case, list_historical_cases  # noqa: E402


EXPECTED_SCORES = {
    "REAL-01": 92,
    "REAL-02": 93,
    "REAL-03": 92,
    "REAL-04": 92,
    "REAL-05": 70,
    "REAL-06": 70,
    "REAL-07": 92,
    "REAL-08": 92,
    "REAL-09": 74,
    "REAL-10": 90,
    "REAL-11": 82,
}
FORBIDDEN_PUBLIC_TEXT = re.compile(
    r"(?:[A-Za-z]:\\|/(?:tmp|home|Users)/|"
    r"\b(?:query|fact|chunk|storage|document|event|target|issue)_id\b)",
    re.IGNORECASE,
)


def _normalized(value: str) -> str:
    return re.sub(r"[^\w%]+", " ", value.casefold()).strip()


def _case_texts(case_file: dict[str, object]) -> list[str]:
    rows: list[str] = []
    for exchange in case_file["question_answer_exchange"]:
        rows.extend(exchange["answers"])
    rows.extend(item["question"] for item in case_file["open_questions"])
    rows.extend(item["title"] for item in case_file["determinant_sources"])
    rows.extend(
        item["document"] for item in case_file["documents_still_needed"]
    )
    conclusion = case_file["conclusion"]
    rows.extend(conclusion["position"])
    rows.extend(conclusion["advice"])
    rows.extend(conclusion["limits"])
    return rows


def test_catalog_presents_eleven_union_case_files_with_business_capabilities() -> None:
    catalog = list_historical_cases()

    assert catalog["result_count"] == 11
    assert catalog["introduction"] == (
        "Onze situations concrètes pour comprendre ce que CFDT Nexus apporte "
        "au délégué syndical."
    )
    assert all(case["capacity"] for case in catalog["cases"])


def test_each_case_has_questions_answers_and_a_union_conclusion() -> None:
    for case_id in EXPECTED_SCORES:
        case_file = get_historical_case(case_id)["union_case_file"]
        exchanges = case_file["question_answer_exchange"]
        conclusion = case_file["conclusion"]

        assert case_file["public_reference"] == f"Dossier {case_id[-2:]}"
        assert len(exchanges) == 3
        assert all(row["question"] for row in exchanges)
        assert all(row["answers"] for row in exchanges)
        assert conclusion["headline"]
        assert conclusion["position"] or case_id in {"REAL-05", "REAL-06"}
        assert conclusion["advice"]
        assert "Conseils de préparation syndicale" in conclusion["warning"]


def test_open_questions_are_honest_and_never_fabricate_an_answer() -> None:
    for case_id in EXPECTED_SCORES:
        detail = get_historical_case(case_id)
        rows = detail["union_case_file"]["open_questions"]

        assert rows
        for row in rows:
            assert row["question"]
            assert row["asked_to"]
            assert row["answer"] in {
                "Réponse indispensable avant de reprendre l’analyse.",
                "Réponse à obtenir ou à confirmer dans le dossier réel.",
            }


def test_exact_repetitions_are_removed_from_the_public_dossier_projection() -> None:
    for case_id in EXPECTED_SCORES:
        rows = _case_texts(get_historical_case(case_id)["union_case_file"])
        normalized = [_normalized(item) for item in rows if _normalized(item)]

        assert len(normalized) == len(set(normalized)), case_id


def test_sources_are_bounded_and_documents_already_found_are_not_requested_again() -> None:
    for case_id in EXPECTED_SCORES:
        case_file = get_historical_case(case_id)["union_case_file"]
        sources = case_file["determinant_sources"]
        documents = case_file["documents_still_needed"]

        assert len(sources) <= 5
        source_titles = [_normalized(item["title"]) for item in sources]
        for document in documents:
            document_key = _normalized(document["document"])
            assert not any(
                len(document_key) > 15
                and (document_key in title or title in document_key)
                for title in source_titles
            )


def test_scores_states_and_validated_summary_remain_unchanged() -> None:
    for case_id, score in EXPECTED_SCORES.items():
        detail = get_historical_case(case_id)

        assert detail["score"] == score
        assert detail["public_summary"]

    assert get_historical_case("REAL-05")["state"] == "SUSPENDU"
    assert get_historical_case("REAL-06")["state"] == "SUSPENDU"
    assert (
        get_historical_case("REAL-09")["state"]
        == "LIMITÉ PAR SOURCE ABSENTE"
    )


def test_suspended_and_limited_cases_keep_a_prudent_conclusion() -> None:
    for case_id in ("REAL-05", "REAL-06"):
        conclusion = get_historical_case(case_id)["union_case_file"]["conclusion"]
        assert conclusion["headline"].startswith("Dossier suspendu")
        assert any("Ne pas conclure" in item for item in conclusion["advice"])

    real09 = get_historical_case("REAL-09")["union_case_file"]["conclusion"]
    assert "procédure interne applicable" in real09["headline"]


def test_badging_case_distinguishes_pause_rule_from_data_reuse() -> None:
    case_file = get_historical_case("REAL-02")["union_case_file"]
    sources = case_file["determinant_sources"]
    documents = case_file["documents_still_needed"]

    assert any("Art. 22 et 23" in item["reference"] for item in sources)
    assert any("tourniquet" in item["practical_use"] for item in sources)
    assert any("CNIL" in item["document"] for item in documents)
    assert all(
        item["status"] != "RETRIEVED" or item["excerpt"]
        for item in sources
    )


def test_tag_case_uses_disciplinary_text_without_harassment_misclassification() -> None:
    case_file = get_historical_case("REAL-03")["union_case_file"]
    sources_text = json.dumps(
        case_file["determinant_sources"],
        ensure_ascii=False,
    ).casefold()

    assert "art. 35 et 36" in sources_text
    assert "injures" in sources_text
    assert "dégradation volontaire" in sources_text
    assert "harcèlement" not in sources_text
    assert "agissements répétés" not in sources_text


def test_schedule_cases_use_readable_exact_passages_instead_of_ocr_tables() -> None:
    for case_id in ("REAL-04", "REAL-08"):
        sources = get_historical_case(case_id)["union_case_file"][
            "determinant_sources"
        ]
        serialized = json.dumps(sources, ensure_ascii=False)

        assert "sept jours par semaine" in serialized
        assert "Charge de travail et effectifs" in serialized
        assert "(cid:" not in serialized
        assert "52,18 semaines" not in serialized
        assert "190 190" not in serialized


def test_ppe_case_starts_with_the_relevant_article_not_phone_rules() -> None:
    source = get_historical_case("REAL-07")["union_case_file"][
        "determinant_sources"
    ][0]

    assert source["reference"] == "Page 2 · Art. 4"
    assert "équipements de protection" in source["excerpt"].casefold()
    assert "téléphone" not in source["excerpt"].casefold()
    assert "cabine" not in source["excerpt"].casefold()


def test_alcohol_and_fatigue_cases_now_show_determinant_collective_texts() -> None:
    alcohol = get_historical_case("REAL-10")["union_case_file"]
    fatigue = get_historical_case("REAL-11")["union_case_file"]
    alcohol_text = json.dumps(alcohol["determinant_sources"], ensure_ascii=False)
    fatigue_text = json.dumps(fatigue["determinant_sources"], ensure_ascii=False)

    assert "Art. 10" in alcohol_text
    assert "contre-expertise" in alcohol_text
    assert "Art. 34 et 35" in alcohol_text
    assert "Art. 35 et 36" in fatigue_text
    assert "fatigue excessive" in fatigue_text
    assert "Charge de travail et effectifs" in fatigue_text


def test_union_advice_is_specific_to_each_case_not_a_repeated_footer() -> None:
    advice_sets = []
    for case_id in EXPECTED_SCORES:
        advice = get_historical_case(case_id)["union_case_file"]["conclusion"][
            "advice"
        ]
        advice_sets.append(tuple(_normalized(item) for item in advice))
        assert not any("ne pas injecter" in item for item in advice_sets[-1])
        assert not any("ne pas promettre" in item for item in advice_sets[-1])

    assert len(advice_sets) == len(set(advice_sets))


def test_public_dossiers_expose_no_technical_identifier_or_sensitive_path() -> None:
    for case_id in EXPECTED_SCORES:
        serialized = json.dumps(
            get_historical_case(case_id)["union_case_file"],
            ensure_ascii=False,
        )
        assert not FORBIDDEN_PUBLIC_TEXT.search(serialized)
        assert "evaluation_expectations" not in serialized
        assert "known_outcome" not in serialized


def test_interface_defaults_to_the_union_presentation_and_keeps_technical_details_closed() -> None:
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    script = (APP_DIR / "app.js").read_text(encoding="utf-8")
    styles = (APP_DIR / "styles.css").read_text(encoding="utf-8")

    assert "Dossiers syndicaux de démonstration" in html
    assert "Onze situations concrètes" in html
    assert "Voir le dossier traité" in script
    assert "Questions et réponses du dossier" in script
    assert "Conclusion et conseils syndicaux" in script
    assert 'document.createElement("details")' in script
    assert "Voir l’analyse technique validée" in script
    assert "union-case-conclusion" in styles


def test_copy_and_print_use_the_public_dossier_projection_only() -> None:
    script = (APP_DIR / "app.js").read_text(encoding="utf-8")
    styles = (APP_DIR / "styles.css").read_text(encoding="utf-8")

    copy_function = script.split("function historicalCaseText", 1)[1].split(
        "function renderHistoricalDetail", 1
    )[0]
    assert "union_case_file" in copy_function
    assert "detailed_analysis" not in copy_function
    assert "CONCLUSION ET CONSEILS SYNDICAUX" in copy_function
    assert (
        "body.print-historical-case .history-technical-analysis" in styles
    )


def test_new_analysis_endpoint_remains_isolated_from_historical_dossiers() -> None:
    server = (APP_DIR / "server.py").read_text(encoding="utf-8")
    script = (APP_DIR / "app.js").read_text(encoding="utf-8")
    post_handler = server.split("def do_POST", 1)[1]
    request_analysis = script.split(
        "async function requestNexusAnalysis", 1
    )[1].split("function setStatus", 1)[0]

    assert "union_case_file" not in post_handler
    assert "historical" not in request_analysis.casefold()
    assert "union_case_file" not in request_analysis
