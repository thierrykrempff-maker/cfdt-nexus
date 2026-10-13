"""Recherche libre dans l'archive des PV : module, routes HTTP et garde-fous.

Corpus et réponses FICTIFS : aucun vrai PV n'entre dans le dépôt.
"""

from __future__ import annotations

import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import threading
import urllib.error
import urllib.request

import pytest


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "nexus-local-interface"
sys.path.insert(0, str(APP_DIR))


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, APP_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = _load("nexus_pv_archive_search", "pv_archive_search.py")

ARCHIVE_ROWS = [
    {
        "date": "2016-03-31",
        "precision_date": "jour",
        "fichier": "PV du CE 2016\\03\\2016.03.31 Compte Rendu CE.doc",
        "page": 2,
        "notions": ["connaissances", "installations"],
        "extrait": "Fictif : la direction présente le contrôle des connaissances sur les installations.",
    },
    {
        "date": "2022-06-29",
        "precision_date": "jour",
        "fichier": "PV du CSE 2022\\CSE extra\\Politique sociale.pdf",
        "page": 30,
        "notions": ["connaissances"],
        "extrait": "Fictif : l'évaluation des compétences est évoquée par les élus du CSE.",
    },
]


class _FakeArchive:
    def __init__(self, rows=ARCHIVE_ROWS):
        self.posts: list[dict[str, object]] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _answer(self, payload):
                raw = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                self._answer({"ok": True, "pv_indexes": 783})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.posts.append({"path": self.path, "headers": dict(self.headers), "body": body})
                self._answer({"ok": True, "points": {point["id"]: rows for point in body["points"]}})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def archive(monkeypatch):
    fake = _FakeArchive()
    monkeypatch.setenv("NEXUS_PV_ARCHIVE_ENABLED", "true")
    monkeypatch.setenv("NEXUS_PV_ARCHIVE_URL", fake.url)
    yield fake
    fake.close()


# --- mots-clés ------------------------------------------------------------------------------------


def test_query_concepts_keeps_distinctive_words_only() -> None:
    concepts = MODULE.query_concepts("Comment se passe le suivi des connaissances des opérateurs sur les installations ?")
    assert concepts == ["passe", "suivi", "connaissances", "operateurs", "installations"]
    assert "comment" not in concepts and "des" not in concepts


def test_query_concepts_are_capped_and_prefer_long_words() -> None:
    words = [f"mot{chr(97 + i)}" * 1 for i in range(8)] + ["extraordinairement", "particulierement", "responsabilites", "anticonstitutionnellement"]
    concepts = MODULE.query_concepts(" ".join(words))
    assert len(concepts) == MODULE.MAX_CONCEPTS == 12
    assert {"extraordinairement", "particulierement", "responsabilites", "anticonstitutionnellement"} <= set(concepts)


@pytest.mark.parametrize("count,expected", [(1, 1), (2, 2), (3, 2), (4, 2), (5, 3), (6, 3), (7, 4), (12, 4)])
def test_required_matches_grows_slowly(count: int, expected: int) -> None:
    assert MODULE.required_matches(count) == expected


# --- recherche ------------------------------------------------------------------------------------


def test_disabled_by_default_never_calls_the_service(monkeypatch) -> None:
    fake = _FakeArchive()
    monkeypatch.delenv("NEXUS_PV_ARCHIVE_ENABLED", raising=False)
    monkeypatch.setenv("NEXUS_PV_ARCHIVE_URL", fake.url)
    try:
        result = MODULE.search_pv_archive("suivi des connaissances")
        status = MODULE.archive_status()
    finally:
        fake.close()
    assert result["status"] == "DISABLED" and result["results"] == []
    assert status == {"enabled": False, "available": False}
    assert fake.posts == []


def test_search_returns_local_passages_with_visible_archive_label(archive) -> None:
    result = MODULE.search_pv_archive("suivi des connaissances des installations")
    assert result["status"] == "READY"
    assert result["concepts"] == ["suivi", "connaissances", "installations"]
    assert result["required_matches"] == 2
    first = result["results"][0]
    assert first["title"] == "2016.03.31 Compte Rendu CE"  # nom du PV, jamais de chemin
    assert first["instance"] == "CE · archive PV" and first["date"] == "2016-03-31" and first["reference"] == "p. 2"
    assert result["results"][1]["instance"] == "CSE · archive PV"
    assert "pas une norme juridique" in result["notice"] or "ne constituent pas une norme" in result["notice"]
    post = archive.posts[0]
    assert post["path"] == "/api/passages"
    headers = {key.lower(): value for key, value in post["headers"].items()}
    assert headers["x-nexus-server"] == "1" and "origin" not in headers
    assert post["body"]["points"][0]["min_matches"] == 2 and post["body"]["limit"] == 6


def test_search_forwards_year_bounds_and_caps_the_limit(archive) -> None:
    MODULE.search_pv_archive("télétravail charte", since="2020", until=2023, limit=500)
    body = archive.posts[0]["body"]
    assert body["since"] == 2020 and body["until"] == 2023 and body["limit"] == MODULE.MAX_LIMIT
    MODULE.search_pv_archive("télétravail charte", since="abc", until="1500", limit="x")
    body = archive.posts[1]["body"]
    assert "since" not in body and "until" not in body and body["limit"] == MODULE.DEFAULT_LIMIT


def test_empty_or_stopword_only_query_is_rejected_without_calling_the_service(archive) -> None:
    for query in ("", "   ", "le la un", "comment faire ?", None, 42):
        result = MODULE.search_pv_archive(query)
        assert result["status"] == "EMPTY_QUERY" and result["results"] == [], query
    assert archive.posts == []


def test_unavailable_or_non_local_service_never_raises(monkeypatch) -> None:
    monkeypatch.setenv("NEXUS_PV_ARCHIVE_ENABLED", "true")
    monkeypatch.setenv("NEXUS_PV_ARCHIVE_URL", "http://127.0.0.1:9")
    assert MODULE.search_pv_archive("connaissances installations")["status"] == "UNAVAILABLE"
    assert MODULE.archive_status() == {"enabled": True, "available": False}
    for url in ("http://example.org:8791", "https://127.0.0.1:8791", "http://192.168.1.10:8791"):
        monkeypatch.setenv("NEXUS_PV_ARCHIVE_URL", url)
        assert MODULE.search_pv_archive("connaissances installations")["status"] == "UNAVAILABLE", url


def test_malformed_service_answer_is_ignored(monkeypatch) -> None:
    fake = _FakeArchive(rows=[{"extrait": ""}, "pas un objet", {"fichier": "x.pdf"}])
    monkeypatch.setenv("NEXUS_PV_ARCHIVE_ENABLED", "true")
    monkeypatch.setenv("NEXUS_PV_ARCHIVE_URL", fake.url)
    try:
        result = MODULE.search_pv_archive("connaissances installations")
    finally:
        fake.close()
    assert result["status"] == "READY" and result["results"] == []


def test_status_reports_available_when_service_answers(archive) -> None:
    assert MODULE.archive_status() == {"enabled": True, "available": True, "indexed_documents": 783}


# --- routes HTTP du serveur Nexus -------------------------------------------------------------------


@pytest.fixture
def nexus_http():
    server = _load("nexus_pv_archive_server_under_test", "server.py")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.NexusHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    yield base
    httpd.shutdown()
    httpd.server_close()


def _post(base: str, path: str, payload) -> tuple[int, dict]:
    request = urllib.request.Request(
        base + path, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def test_http_status_and_search_routes(archive, nexus_http) -> None:
    with urllib.request.urlopen(nexus_http + "/api/pv-archive/status", timeout=30) as response:
        status = json.loads(response.read())
    assert status == {"ok": True, "enabled": True, "available": True, "indexed_documents": 783}

    code, body = _post(nexus_http, "/api/pv-archive/search", {"query": "connaissances installations", "limit": 2})
    assert code == 200 and body["ok"] is True
    assert body["pv_archive"]["status"] == "READY"
    assert [row["origin"] for row in body["pv_archive"]["results"]] == ["PV_ARCHIVE", "PV_ARCHIVE"]


def test_http_search_is_disabled_by_default_and_rejects_bad_bodies(monkeypatch, nexus_http) -> None:
    monkeypatch.delenv("NEXUS_PV_ARCHIVE_ENABLED", raising=False)
    code, body = _post(nexus_http, "/api/pv-archive/search", {"query": "connaissances installations"})
    assert code == 200 and body["pv_archive"]["status"] == "DISABLED"
    code, body = _post(nexus_http, "/api/pv-archive/search", ["pas", "un", "objet"])
    assert code == 400 and body["ok"] is False
    code, _ = _post(nexus_http, "/api/pv-archive/inconnu", {})
    assert code == 404
