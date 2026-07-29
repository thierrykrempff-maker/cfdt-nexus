from __future__ import annotations

import json
import re
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "nexus-local-interface"
sys.path.insert(0, str(APP_DIR))

from historical_cases import (  # noqa: E402
    CASE_PRESENTATION,
    FORBIDDEN_PUBLIC_KEYS,
    PUBLIC_SUMMARY_FIELDS,
    RAW_ROOT,
    get_historical_case,
    list_historical_cases,
)
from server import NexusHandler  # noqa: E402


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
EXPECTED_STATES = {
    "REAL-01": "ANALYSÉ",
    "REAL-02": "ANALYSÉ",
    "REAL-03": "ANALYSÉ",
    "REAL-04": "ANALYSÉ",
    "REAL-05": "SUSPENDU",
    "REAL-06": "SUSPENDU",
    "REAL-07": "ANALYSÉ",
    "REAL-08": "ANALYSÉ",
    "REAL-09": "LIMITÉ PAR SOURCE ABSENTE",
    "REAL-10": "ANALYSÉ",
    "REAL-11": "ANALYSÉ",
}
FORBIDDEN_TEXT = re.compile(
    r"(?:[A-Za-z]:\\|/(?:tmp|home|Users)/|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,})",
    re.IGNORECASE,
)


def _all_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key).lower()
            yield from _all_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _all_keys(nested)


def _json_get(base_url: str, path: str):
    try:
        with urllib.request.urlopen(base_url + path, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


@pytest.fixture()
def historical_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), NexusHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_catalog_contains_exactly_the_eleven_validated_cases():
    catalog = list_historical_cases()
    assert [case["id"] for case in catalog["cases"]] == list(EXPECTED_SCORES)
    assert catalog["result_count"] == 11
    assert catalog["score_average"] == 85.36
    assert catalog["product_version"] == "1.0.0"


def test_scores_paths_and_states_match_the_v1_results():
    cases = {case["id"]: case for case in list_historical_cases()["cases"]}
    assert {case_id: case["score"] for case_id, case in cases.items()} == EXPECTED_SCORES
    assert {case_id: case["state"] for case_id, case in cases.items()} == EXPECTED_STATES
    assert cases["REAL-02"]["employee_path"] == "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE"
    assert cases["REAL-04"]["employee_path"] == "QUESTION_SALARIE"


def test_catalog_warning_explains_the_non_precedential_nature():
    catalog = list_historical_cases()
    assert "ni une jurisprudence" in catalog["warning"]
    assert "ni une garantie de résultat" in catalog["warning"]
    assert "Il ne garantit pas l’issue réelle" in catalog["score_explanation"]


@pytest.mark.parametrize(
    ("query", "expected_id"),
    [
        ("alcool", "REAL-01"),
        ("badgeage", "REAL-02"),
        ("horaires", "REAL-04"),
        ("CSSCT", "REAL-05"),
        ("EPI", "REAL-07"),
        ("procédure", "REAL-09"),
        ("congés", "REAL-06"),
    ],
)
def test_simple_search_finds_a_relevant_case(query, expected_id):
    ids = {case["id"] for case in list_historical_cases(query=query)["cases"]}
    assert expected_id in ids


@pytest.mark.parametrize(
    ("category", "expected_ids"),
    [
        ("disciplinary", {"REAL-01", "REAL-02", "REAL-03", "REAL-10", "REAL-11"}),
        ("personal_data", {"REAL-02"}),
        ("cse_cssct", {"REAL-05"}),
        ("suspended", {"REAL-05", "REAL-06"}),
    ],
)
def test_filters_are_deterministic(category, expected_ids):
    result = list_historical_cases(category=category)
    assert {case["id"] for case in result["cases"]} == expected_ids
    assert result["result_count"] == len(expected_ids)


def test_unknown_filter_is_rejected():
    with pytest.raises(ValueError, match="Filtre historique inconnu"):
        list_historical_cases(category="technical")


def test_detail_uses_only_the_validated_public_summary():
    for short_id, presentation in CASE_PRESENTATION.items():
        raw = json.loads((RAW_ROOT / presentation["fixture"]).read_text(encoding="utf-8"))
        source = raw["response"]["public_summary"]
        detail = get_historical_case(short_id)
        expected = {
            key: source[key]
            for key in PUBLIC_SUMMARY_FIELDS
            if key in source
        }
        assert detail["public_summary"] == expected


def test_public_projection_excludes_evaluation_and_technical_fields():
    for case_id in EXPECTED_SCORES:
        detail = get_historical_case(case_id)
        keys = set(_all_keys(detail))
        assert not keys.intersection(FORBIDDEN_PUBLIC_KEYS)
        serialized = json.dumps(detail, ensure_ascii=False)
        assert "evaluation_only" not in serialized
        assert "evaluation_expectations" not in serialized
        assert "known_outcome" not in serialized
        assert "detailed_analysis" not in serialized
        assert "public_response_size_bytes" not in serialized


def test_public_projection_contains_no_direct_identifier_or_local_path():
    for case_id in EXPECTED_SCORES:
        serialized = json.dumps(get_historical_case(case_id), ensure_ascii=False)
        assert not FORBIDDEN_TEXT.search(serialized)
        assert "matricule" not in serialized.casefold()
        assert "numéro de téléphone" not in serialized.casefold()
        assert "adresse personnelle" not in serialized.casefold()


def test_special_cases_preserve_the_validated_limits():
    real05 = get_historical_case("REAL-05")
    real06 = get_historical_case("REAL-06")
    real09 = get_historical_case("REAL-09")
    assert real05["state"] == "SUSPENDU"
    assert "Aucune conclusion automatique" in " ".join(real05["special_notes"])
    assert real06["state"] == "SUSPENDU"
    assert "clarification est obligatoire" in " ".join(real06["special_notes"])
    assert real09["state"] == "LIMITÉ PAR SOURCE ABSENTE"
    assert "Aucune procédure ou instruction n’a été fabriquée" in " ".join(
        real09["special_notes"]
    )


def test_historical_cases_are_explicitly_read_only_and_not_reused():
    for case_id in EXPECTED_SCORES:
        detail = get_historical_case(case_id)
        assert detail["automatic_reuse"] is False
        assert "Consultation" in detail["usage"]


def test_http_api_exposes_catalog_filters_and_safe_detail(historical_server):
    status, catalog = _json_get(
        historical_server,
        "/api/historical-cases?query=badgeage&category=personal_data",
    )
    assert status == 200
    assert catalog["result_count"] == 1
    assert catalog["cases"][0]["id"] == "REAL-02"

    status, payload = _json_get(historical_server, "/api/historical-cases/REAL-09")
    assert status == 200
    assert payload["case"]["state"] == "LIMITÉ PAR SOURCE ABSENTE"
    assert "detailed_analysis" not in json.dumps(payload)


def test_http_api_rejects_unknown_cases_and_filters(historical_server):
    status, payload = _json_get(
        historical_server, "/api/historical-cases?category=unknown"
    )
    assert status == 400
    assert payload["ok"] is False
    status, payload = _json_get(
        historical_server, "/api/historical-cases/REAL-99"
    )
    assert status == 404
    assert payload["ok"] is False


def test_interface_contains_search_filters_keyboard_copy_and_print_contracts():
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    script = (APP_DIR / "app.js").read_text(encoding="utf-8")
    assert 'id="historySearch"' in html
    assert 'id="historyFilters"' in html
    assert 'id="historyCopyButton"' in html
    assert 'id="historyPrintButton"' in html
    assert "historyView.addEventListener(\"keydown\"" in script
    assert 'event.key === "Escape"' in script
    assert "navigator.clipboard" in script
    assert "printHistoricalCase" in script


def test_historical_view_is_isolated_from_new_employee_analysis():
    server_source = (APP_DIR / "server.py").read_text(encoding="utf-8")
    script = (APP_DIR / "app.js").read_text(encoding="utf-8")
    post_handler = server_source.split("def do_POST", 1)[1]
    request_analysis = script.split(
        "async function requestNexusAnalysis", 1
    )[1].split("function setStatus", 1)[0]
    assert "historical" not in post_handler.casefold()
    assert "historical" not in request_analysis.casefold()
    assert "currentHistoricalCase" not in request_analysis
    assert 'fetch("/api/analyze"' in request_analysis


def test_existing_employee_paths_remain_present_and_distinct():
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    assert 'data-employee-path="QUESTION_SALARIE"' in html
    assert 'data-employee-path="ASSISTANCE_ENTRETIEN_DISCIPLINAIRE"' in html
