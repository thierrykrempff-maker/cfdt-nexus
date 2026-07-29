from __future__ import annotations

from datetime import datetime, timezone
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "nexus-local-interface"
sys.path.insert(0, str(APP_DIR))

from historical_cases import (  # noqa: E402
    CASE_PRESENTATION,
    get_historical_case,
    refresh_historical_case_sources,
)


def _agreement_source() -> dict[str, object]:
    return {
        "document": "Avenant 2 à l’accord 35 heures — 5x8",
        "excerpt": "Le passage en équipes 5x8 est organisé selon le cycle défini.",
        "article": "Article 4 — Cycle 5x8",
        "location": "Article 4 — Cycle 5x8",
        "source_layer": "accord_entreprise",
        "origin": "bible_accords",
        "official_id": "INEOS-5X8",
        "publication_date": "2014-06-12",
        "date_debut": "2014-07-01",
    }


def _source(
    title: str,
    excerpt: str,
    article: str,
    *,
    layer: str = "accord_entreprise",
) -> dict[str, object]:
    return {
        "document": title,
        "excerpt": excerpt,
        "article": article,
        "location": article,
        "source_layer": layer,
        "origin": "bible_accords",
        "official_id": title,
        "publication_date": "2024-01-01",
        "date_debut": "2024-01-01",
        "is_in_force": True,
    }


def test_refresh_keeps_historical_score_and_analysis_unchanged() -> None:
    before = get_historical_case("REAL-04")
    refreshed = refresh_historical_case_sources(
        "REAL-04",
        source_fetcher=lambda _queries: [_agreement_source()],
        now=datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc),
    )

    assert refreshed["score"] == before["score"] == 92
    assert refreshed["state"] == before["state"]
    assert refreshed["analysis_unchanged"] is True
    assert refreshed["score_unchanged"] is True
    assert refreshed["automatic_reuse"] is False
    assert refreshed["last_refreshed_at"] == "2026-07-29T12:00:00+00:00"
    assert refreshed["current_documentary_analysis"]["sources"]


def test_real02_extracts_available_pause_text_without_inventing_rgpd_notice() -> None:
    refreshed = refresh_historical_case_sources(
        "REAL-02",
        source_fetcher=lambda _queries: [
            _source(
                "Accord temps de travail — pauses et badgeage",
                "Les pauses et leur décompte par badgeage sont décrits dans cette clause.",
                "Article 8 — Pauses",
            )
        ],
    )

    assert refreshed["current_documentary_analysis"]["sources"]
    assert any(
        "RGPD" in item["requested_document"]
        and item["availability_status"] == "ABSENT"
        for item in refreshed["still_absent"]
    )


@pytest.mark.parametrize("case_id", sorted(CASE_PRESENTATION))
def test_all_eleven_cases_preserve_score_and_state_during_empty_refresh(
    case_id: str,
) -> None:
    before = get_historical_case(case_id)
    refreshed = refresh_historical_case_sources(
        case_id,
        source_fetcher=lambda _queries: [],
        now=datetime(2026, 7, 29, tzinfo=timezone.utc),
    )

    assert refreshed["score"] == before["score"]
    assert refreshed["state"] == before["state"]
    assert refreshed["current_documentary_analysis"]["retrieved_count"] == 0


def test_refresh_payload_contains_no_fixture_path_or_reserved_analysis() -> None:
    refreshed = refresh_historical_case_sources(
        "REAL-04",
        source_fetcher=lambda _queries: [_agreement_source()],
    )
    serialized = json.dumps(refreshed, ensure_ascii=False)

    assert "source_to_facts_baseline" not in serialized
    assert "detailed_analysis" not in serialized
    assert "evaluation_expectations" not in serialized
    assert "known_outcome" not in serialized


def test_real05_keeps_suspension_while_exposing_existing_cse_agreement() -> None:
    refreshed = refresh_historical_case_sources(
        "REAL-05",
        source_fetcher=lambda _queries: [
            _source(
                "Accord sur la mise en place du CSE",
                "La périodicité des réunions du CSE est définie par cet article.",
                "Article 5 — Périodicité des réunions",
            )
        ],
    )

    assert refreshed["state"] == "SUSPENDU"
    assert refreshed["analysis_unchanged"] is True
    assert refreshed["current_documentary_analysis"]["sources"]


def test_real06_does_not_choose_the_meaning_of_ten_percent_rule() -> None:
    refreshed = refresh_historical_case_sources(
        "REAL-06",
        source_fetcher=lambda _queries: [
            _source(
                "Modification de la période de référence des congés annuels",
                "La période de référence est modifiée sans définir la règle des 10 %.",
                "Article 2",
            )
        ],
    )

    assert refreshed["state"] == "SUSPENDU"
    assert refreshed["score"] == 70
    assert refreshed["analysis_unchanged"] is True
    assert any(
        item["availability_status"] in {"ABSENT", "NEEDS_CLARIFICATION"}
        for item in refreshed["current_documentary_analysis"][
            "document_resolutions"
        ]
    )


def test_real07_does_not_treat_generic_internal_rules_as_an_epi_instruction() -> None:
    refreshed = refresh_historical_case_sources(
        "REAL-07",
        source_fetcher=lambda _queries: [
            _source(
                "Règlement intérieur — accès au site",
                "Le badge est obligatoire pour accéder au site.",
                "Article 2",
            )
        ],
    )

    assert any(
        "Consigne EPI" in item["requested_document"]
        and item["availability_status"] == "ABSENT"
        for item in refreshed["still_absent"]
    )


def test_real09_still_reports_missing_chemical_procedure_honestly() -> None:
    refreshed = refresh_historical_case_sources(
        "REAL-09",
        source_fetcher=lambda _queries: [],
    )

    assert refreshed["state"] == "LIMITÉ PAR SOURCE ABSENTE"
    assert any(
        "chimique" in item["requested_document"].casefold()
        and item["availability_status"] == "ABSENT"
        for item in refreshed["still_absent"]
    )


def test_ui_refresh_is_separate_from_new_analysis_payload() -> None:
    script = (APP_DIR / "app.js").read_text(encoding="utf-8")
    request_analysis = script.split(
        "async function requestNexusAnalysis", 1
    )[1].split("function setStatus", 1)[0]

    assert "refreshHistoricalSources" in script
    assert "/refresh-sources" in script
    assert "currentHistoricalCase" not in request_analysis
    assert "historical" not in request_analysis.casefold()
