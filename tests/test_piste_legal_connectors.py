from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import urllib.error

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "automation" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import judilibre_connector as judilibre  # noqa: E402
import legifrance_connector as legifrance  # noqa: E402
from piste_oauth import PisteCredentials, PisteOAuthClient, PisteOAuthError  # noqa: E402


class Response:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def credentials() -> PisteCredentials:
    return PisteCredentials("client-id-test", "secret-test", "https://oauth.test/token")


def test_oauth_token_is_cached_only_in_memory_and_renewed() -> None:
    calls = []
    now = [1000.0]

    def opener(request, **_kwargs):
        calls.append(request)
        return Response({"access_token": "token-test", "token_type": "Bearer", "expires_in": 120})

    client = PisteOAuthClient(credentials(), opener=opener, clock=lambda: now[0])
    assert client.token()["from_cache"] is False
    assert client.token()["from_cache"] is True
    assert len(calls) == 1
    now[0] = 1070
    assert client.token()["from_cache"] is False
    assert len(calls) == 2
    assert not hasattr(client, "token_cache_path")


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [(400, "authentication_failed"), (401, "authentication_failed"), (403, "forbidden"), (429, "quota_exceeded"), (503, "unavailable")],
)
def test_oauth_classifies_http_failures(status_code: int, expected: str) -> None:
    def opener(*_args, **_kwargs):
        raise urllib.error.HTTPError("https://oauth.test", status_code, "failure", {}, io.BytesIO())

    client = PisteOAuthClient(credentials(), opener=opener, retry_count=0)
    with pytest.raises(PisteOAuthError) as exc:
        client.token()
    assert exc.value.status == expected
    assert "secret-test" not in str(exc.value)


def test_oauth_missing_credentials_is_not_configured() -> None:
    client = PisteOAuthClient(PisteCredentials(None, None))
    with pytest.raises(PisteOAuthError, match="absents") as exc:
        client.token()
    assert exc.value.status == "not_configured"


def test_legifrance_environment_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEGIFRANCE_CLIENT_ID", "specific")
    monkeypatch.setenv("LEGIFRANCE_CLIENT_SECRET", "specific-secret")
    monkeypatch.setenv("PISTE_CLIENT_ID", "common")
    monkeypatch.setenv("PISTE_CLIENT_SECRET", "common-secret")
    monkeypatch.setenv("CFDT_NEXUS_LEGIFRANCE_CLIENT_ID", "legacy")
    monkeypatch.setenv("CFDT_NEXUS_LEGIFRANCE_CLIENT_SECRET", "legacy-secret")
    config = legifrance.LegifranceConfig.from_env()
    assert config.client_id == "specific"
    assert config.client_secret == "specific-secret"


def test_judilibre_environment_precedence_and_independence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JUDILIBRE_CLIENT_ID", "judilibre-specific")
    monkeypatch.setenv("JUDILIBRE_CLIENT_SECRET", "judilibre-secret")
    monkeypatch.setenv("LEGIFRANCE_CLIENT_ID", "legifrance-specific")
    config = judilibre.JudilibreConfig.from_env()
    assert config.client_id == "judilibre-specific"
    assert config.client_id_source == "JUDILIBRE_CLIENT_ID"


def test_legifrance_code_search_payload_uses_official_facets_and_pagination() -> None:
    payload = legifrance.build_search_payload("L1221-1", 5, page=3)
    search = payload["recherche"]
    assert payload["fond"] == "CODE_DATE"
    assert search["filtres"] == [{"facette": "TEXT_NOM_CODE", "valeurs": ["Code du travail"]}]
    assert search["pageNumber"] == 3
    assert search["typePagination"] == "ARTICLE"
    assert search["operateur"] == "ET"


def test_legifrance_idcc_44_payload_is_structured() -> None:
    payload = legifrance.build_idcc_search_payload("44", "travail de nuit", 5)
    assert payload["fond"] == "KALI"
    assert payload["recherche"]["champs"][0]["typeChamp"] == "IDCC"
    assert payload["recherche"]["champs"][0]["criteres"][0]["valeur"] == "44"


def test_connectors_no_longer_write_oauth_token_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        PisteOAuthClient,
        "token",
        lambda self, force_refresh=False: {
            "access_token": "memory-only",
            "token_type": "Bearer",
            "expires_in": 3600,
            "from_cache": False,
        },
    )
    legi = legifrance.LegifranceClient(
        legifrance.LegifranceConfig("id", "secret", cache_dir=Path("unused"))
    )
    judi = judilibre.JudilibreClient(
        judilibre.JudilibreConfig("id", "secret", cache_dir=Path("unused"))
    )
    assert legi.authenticate()["access_token"] == "memory-only"
    assert judi.authenticate()["access_token"] == "memory-only"


def test_judilibre_search_forwards_filters_and_pagination(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = judilibre.JudilibreClient(
        judilibre.JudilibreConfig("id", "secret", cache_dir=tmp_path)
    )
    captured = {}

    def fake_get(endpoint, params=None):
        captured.update({"endpoint": endpoint, "params": params})
        return {"results": []}

    monkeypatch.setattr(client, "_get_json", fake_get)
    client.search_decision_hits(
        "modification contrat",
        4,
        page=2,
        jurisdiction="cc",
        chamber="soc",
        date_start="2020-01-01",
        date_end="2025-12-31",
        decision_number="99-41.146",
    )
    assert captured["endpoint"] == "/search"
    assert captured["params"] == {
        "query": "modification contrat",
        "page_size": 4,
        "page": 2,
        "jurisdiction": "cc",
        "chamber": "soc",
        "date_start": "2020-01-01",
        "date_end": "2025-12-31",
        "number": "99-41.146",
    }


def test_normalized_sources_keep_official_provenance() -> None:
    decision = judilibre.normalize_decision_payload({
        "id": "decision-1",
        "jurisdiction": "cc",
        "chamber": "soc",
        "decision_date": "2024-01-02",
        "number": "22-00.001",
        "formation": "formation restreinte",
        "themes": ["contrat de travail"],
        "pseudonymization": {"status": "done"},
        "text": "Texte officiel de la décision.",
    })
    assert decision["source"] == "judilibre"
    assert decision["official_reference"] == "JUDILIBRE:decision-1"
    assert decision["formation"] == "formation restreinte"
    assert decision["pseudonymization"] == {"status": "done"}
