"""Comparaison d'accords et contrôle des interférences : moteur, service d'archive fictif et routes HTTP.

Accords et réponses FICTIFS : aucun vrai accord n'entre dans le dépôt.
"""

from __future__ import annotations

import base64
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
sys.path.insert(0, str(ROOT))


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, APP_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


A = _load("nexus_agreement_compare", "agreement_compare.py")

OLD = """ACCORD RELATIF AU TELETRAVAIL
Préambule : les parties souhaitent encadrer le télétravail occasionnel au sein de l'établissement de Sarralbe pour tous les salariés éligibles.
Article 1 - Champ d'application
Le présent accord s'applique à tous les salariés éligibles.
Article 2 - Nombre de jours
Le salarié peut télétravailler 2 jours par semaine.
Article 3 - Indemnité
Une indemnité de 10 euros par mois est versée au salarié.
Article 4 - Durée
Le présent accord est conclu pour une durée indéterminée.
"""

NEW = """ACCORD RELATIF AU TELETRAVAIL
Article 1 - Champ d'application
Le présent accord s'applique à tous les salariés éligibles.
Article 2 - Nombre de jours
Le salarié doit télétravailler 3 jours par semaine.
Article 3 - Indemnité
Une indemnité de 15 euros par mois est versée au salarié.
Article 5 - Équipement
L'employeur fournit un écran. Cet accord annule et remplace l'accord du 14/02/2022.
"""

AVENANT = """AVENANT N°1 A L'ACCORD TELETRAVAIL
Article 2 - Nombre de jours
Le salarié peut télétravailler 3 jours par semaine.
"""

OTHER = "Article 7 - Indemnité de transport\nUne indemnité de 12 euros par mois est versée aux salariés qui télétravaillent."


def types(result):
    return {(c["type"], c["article"]) for c in result["modifications"]}


# --- découpage en articles -------------------------------------------------------------------------


def test_articles_are_split_with_preamble_and_titles() -> None:
    articles = A.parse_articles(OLD)
    assert [a["label"] for a in articles] == ["Préambule", "Article 1", "Article 2", "Article 3", "Article 4"]
    assert articles[2]["title"] == "Nombre de jours" and "2 jours" in articles[2]["body"]


def test_page_markers_and_page_numbers_are_ignored() -> None:
    text = "Article 1 - Objet\nTexte un.\n--- page 2 ---\n12\nSuite du texte.\n\fArticle 2 - Durée\nTexte deux."
    articles = A.parse_articles(text)
    assert [a["label"] for a in articles] == ["Article 1", "Article 2"]
    assert "page 2" not in articles[0]["body"] and articles[0]["body"].endswith("Suite du texte.")


def test_text_without_article_headings_falls_back_to_passages() -> None:
    paragraphs = "\n\n".join(f"Paragraphe {i} " + "mot " * 80 for i in range(6))
    articles = A.parse_articles(paragraphs)
    assert articles and all(a["label"].startswith("Passage") for a in articles)


def test_citation_of_a_code_article_is_not_a_heading() -> None:
    text = "Article 1 - Objet\nTexte.\nL'article L. 3121-1 du code du travail s'applique.\nArticle 2 - Durée\nTexte."
    assert [a["label"] for a in A.parse_articles(text)] == ["Article 1", "Article 2"]


# --- valeurs chiffrées ----------------------------------------------------------------------------


def test_figures_are_normalised() -> None:
    found = A.figures("Prime de 1 200,50 € ; 10 euros ; 2 jours ; 35 heures ; 3,5 %. Le 12 mars.")
    assert {("1200.5", "€"), ("10", "€"), ("2", "jour"), ("35", "heure"), ("3.5", "%")} <= set(found)
    assert not A.figures("Article 12 du texte, page 3")  # un numéro d'article n'est pas une valeur


# --- comparaison ----------------------------------------------------------------------------------


def test_replacement_reports_changed_added_and_removed_articles() -> None:
    result = A.compare_texts(OLD, NEW, old_label="2022.02.14_Accord télétravail.pdf", new_label="2025.01.01_Accord télétravail.pdf")
    assert result["status"] == "READY" and result["mode"] == "remplacement"
    assert types(result) == {("modifie", "Article 2"), ("modifie", "Article 3"), ("supprime", "Article 4"),
                             ("supprime", "Préambule"), ("ajoute", "Article 5")}
    assert result["resume"]["inchanges"] == 1 and result["resume"]["valeurs_modifiees"] == 2
    by_article = {c["article"]: c for c in result["modifications"]}
    assert by_article["Article 2"]["valeurs"] == ["jour : 2 → 3"]
    assert by_article["Article 2"]["termes_d_obligation"] == ["peut → doit"]
    assert by_article["Article 3"]["valeurs"] == ["€ : 10 → 15"]
    assert "10 euros" in by_article["Article 3"]["avant"][0] and "15 euros" in by_article["Article 3"]["apres"][0]
    assert any("valeur(s) chiffrée(s)" in point for point in result["points_attention"])
    assert any("obligation" in point for point in result["points_attention"])


def test_identical_texts_report_no_difference() -> None:
    result = A.compare_texts(OLD, OLD, old_label="a.pdf", new_label="b.pdf")
    assert result["modifications"] == [] and result["resume"]["inchanges"] == 5
    assert "Aucune différence" in result["points_attention"][0]


def test_ocr_noise_and_punctuation_do_not_create_changes() -> None:
    noisy = OLD.replace("Le salarié peut", "Le  salarié  peut").replace("indéterminée.", "indéterminée")
    assert A.compare_texts(OLD, noisy, old_label="a.pdf", new_label="b.pdf")["modifications"] == []


def test_a_one_digit_change_is_never_hidden_by_text_similarity() -> None:
    long_clause = "Le salarié perçoit une prime " + "de sujétion et d'astreinte pour chaque semaine travaillée " * 3
    old = f"Article 1 - Prime\n{long_clause} de 100 euros."
    new = f"Article 1 - Prime\n{long_clause} de 190 euros."
    result = A.compare_texts(old, new, old_label="a.pdf", new_label="b.pdf")
    assert result["modifications"][0]["valeurs"] == ["€ : 100 → 190"]


def test_an_avenant_does_not_report_untouched_articles_as_removed() -> None:
    result = A.compare_texts(OLD, AVENANT, old_label="2022.02.14_Accord télétravail.pdf",
                             new_label="2025.05.07 - Avenant à l'accord relatif au télétravail.pdf")
    assert result["mode"] == "avenant"
    assert types(result) == {("modifie", "Article 2")}
    assert result["resume"]["supprimes"] == 0 and result["resume"]["non_vises_par_l_avenant"] == 4
    assert any("avenant" in point.lower() and "restent applicables" in point for point in result["points_attention"])


def test_empty_or_unreadable_text_is_invalid() -> None:
    assert A.compare_texts("", NEW, old_label="a.pdf", new_label="b.pdf")["status"] == "INVALID"
    assert A.compare_texts(OLD, "   \n ", old_label="a.pdf", new_label="b.pdf")["status"] == "INVALID"


# --- textes cités ----------------------------------------------------------------------------------


def test_citations_are_found_with_their_effect_and_matched_to_the_archive() -> None:
    documents = [{"id": "x" * 32, "titre": "Accord télétravail", "type": "Accord", "date": "2022-02-14"}]
    text = (
        "Article 9 - Dispositions finales\nCet accord annule et remplace l'accord télétravail du 14/02/2022. "
        "Le protocole d'accord signé le 1er mars 2021 demeure en vigueur. "
        "L'avenant du 03.05.2019 est dénoncé par les parties."
    )
    citations = {c["date"]: c for c in A.find_citations(text, documents)}
    assert citations["2022-02-14"]["effet"] == "remplace" and citations["2022-02-14"]["dans_l_archive"] is True
    assert citations["2022-02-14"]["documents"] == ["Accord télétravail (Accord)"]
    assert citations["2021-03-01"]["effet"] == "maintient en vigueur" and citations["2021-03-01"]["dans_l_archive"] is False
    assert citations["2019-05-03"]["effet"] == "dénonce"


def test_invalid_dates_in_citations_are_ignored() -> None:
    assert A.find_citations("Cet accord du 31/02/2022 remplace.", []) == []


# --- service d'archive fictif ----------------------------------------------------------------------

DOCS = {
    "a" * 16: {"fichier": "2022.02.14_Accord télétravail.pdf", "date": "2022-02-14", "texte": OLD},
    "b" * 16: {"fichier": "2025.01.01_Accord télétravail.pdf", "date": "2025-01-01", "texte": NEW},
    "c" * 16: {"fichier": "2025.05.07 - Avenant à l'accord relatif au télétravail.pdf", "date": "2025-05-07", "texte": AVENANT},
    "d" * 16: {"fichier": "2023.03.01_Accord transport.pdf", "date": "2023-03-01", "texte": OTHER},
}
PV_ROW = {"date": "2024-05-02", "precision_date": "jour", "fichier": "PV du CSE 2024\\PV CSE 02.05.2024.pdf", "page": 4,
          "notions": ["teletravail"], "extrait": "Fictif : la direction présente le bilan du télétravail aux élus du CSE."}


class _FakeArchive:
    def __init__(self):
        self.calls: list[dict[str, object]] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, payload, status=200):
                raw = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                outer.calls.append({"get": self.path})
                docs = [{"id": i, "fichier": d["fichier"], "date": d["date"], "precision_date": "jour", "caracteres": len(d["texte"])}
                        for i, d in DOCS.items()]
                self._send({"ok": True, "documents": docs})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.calls.append({"post": self.path, "body": body})
                if self.path == "/api/document":
                    doc = DOCS.get(body["id"])
                    if not doc:
                        return self._send({"ok": False}, 404)
                    return self._send({"ok": True, "fichier": doc["fichier"], "date": doc["date"], "texte": doc["texte"]})
                if body.get("corpus") == "pv":
                    rows = [PV_ROW]
                else:
                    rows = [{"date": "2023-03-01", "precision_date": "jour", "fichier": "2023.03.01_Accord transport.pdf", "page": 1,
                             "notions": ["indemnite"], "extrait": "Article 7 fictif : une indemnité de 12 euros par mois est versée."}]
                    rows = [r for r in rows if DOCS["d" * 16]["fichier"] not in [DOCS[x]["fichier"] for x in body.get("exclude", []) if x in DOCS]]
                self._send({"ok": True, "points": {p["id"]: rows for p in body["points"]}})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def archive(monkeypatch):
    fake = _FakeArchive()
    monkeypatch.setenv("NEXUS_ACCORDS_ARCHIVE_ENABLED", "true")
    monkeypatch.setenv("NEXUS_PV_ARCHIVE_ENABLED", "true")
    monkeypatch.setenv("NEXUS_PV_ARCHIVE_URL", fake.url)
    yield fake
    fake.close()


def _no_attachment(_attachment):
    raise AssertionError("aucun fichier importé attendu")


def test_list_returns_agreements_newest_first_without_paths(archive) -> None:
    listing = A.list_archive_agreements()
    assert listing["status"] == "READY"
    assert [d["titre"] for d in listing["documents"]] == ["Avenant à l'accord relatif au télétravail", "Accord télétravail", "Accord transport", "Accord télétravail"]
    assert listing["documents"][0]["type"] == "Avenant" and listing["documents"][0]["date"] == "2025-05-07"
    assert all("\\" not in d["titre"] and "/" not in d["titre"] for d in listing["documents"])


def test_compare_two_archive_agreements_checks_interferences_and_meetings(archive) -> None:
    result = A.compare_request({"old": {"id": "a" * 16}, "new": {"id": "b" * 16}}, _no_attachment)
    assert result["status"] == "READY" and result["mode"] == "remplacement"
    assert result["ancien"]["titre"] == "Accord télétravail" and result["nouveau"]["articles"] == 4
    # les deux textes comparés sont exclus de la recherche d'interférences
    passage_calls = [c for c in archive.calls if c.get("post") == "/api/passages" and c["body"]["corpus"] == "accords"]
    assert passage_calls and sorted(passage_calls[0]["body"]["exclude"]) == ["a" * 16, "b" * 16]
    # autre accord sur le même sujet, avec valeur différente détectée (15 € dans le nouveau texte, 12 € ailleurs)
    assert result["interferences_status"] == "READY" and result["interferences"]
    row = result["interferences"][0]["textes"][0]
    assert row["title"] == "Accord transport" and row["origin"] == "ACCORDS_ARCHIVE"
    assert any("€" in note and "15" in note and "12" in note for note in
               (n for item in result["interferences"] for r in item["textes"] for n in r["valeurs_differentes"]))
    assert any("diffèrent" in point for point in result["points_attention"])
    # le texte remplacé (14/02/2022) est retrouvé dans l'archive grâce à sa date
    assert result["citations"][0]["dans_l_archive"] is True
    # contexte des réunions (PV du CE/CSE)
    assert result["reunions"] and result["reunions"][0]["origin"] == "PV_ARCHIVE"


def test_compare_with_an_imported_project_text(archive) -> None:
    def read(attachment):
        return attachment["name"], base64.b64decode(attachment["content_base64"]).decode("utf-8")

    payload = {"old": {"id": "a" * 16},
               "new": {"attachment": {"name": "Projet avenant télétravail.txt", "content_base64": base64.b64encode(AVENANT.encode()).decode()}}}
    result = A.compare_request(payload, read)
    assert result["status"] == "READY" and result["mode"] == "avenant"
    assert result["nouveau"]["titre"] == "Projet avenant télétravail"
    exclude = [c["body"]["exclude"] for c in archive.calls if c.get("post") == "/api/passages" and c["body"]["corpus"] == "accords"][0]
    assert exclude == ["a" * 16]  # un texte importé n'a pas d'identifiant à exclure


def test_pv_context_is_skipped_when_the_pv_archive_is_off(archive, monkeypatch) -> None:
    monkeypatch.delenv("NEXUS_PV_ARCHIVE_ENABLED", raising=False)
    result = A.compare_request({"old": {"id": "a" * 16}, "new": {"id": "b" * 16}}, _no_attachment)
    assert result["status"] == "READY" and result["reunions"] == []
    assert not [c for c in archive.calls if c.get("post") == "/api/passages" and c["body"]["corpus"] == "pv"]


def test_disabled_invalid_and_unavailable_cases_never_raise(monkeypatch) -> None:
    monkeypatch.delenv("NEXUS_ACCORDS_ARCHIVE_ENABLED", raising=False)
    assert A.compare_request({"old": {"id": "a" * 16}, "new": {"id": "b" * 16}}, _no_attachment)["status"] == "DISABLED"
    assert A.list_archive_agreements()["status"] == "DISABLED"
    monkeypatch.setenv("NEXUS_ACCORDS_ARCHIVE_ENABLED", "true")
    monkeypatch.setenv("NEXUS_PV_ARCHIVE_URL", "http://127.0.0.1:9")
    assert A.list_archive_agreements()["status"] == "UNAVAILABLE"
    assert A.compare_request({"old": {"id": "a" * 16}, "new": {"id": "b" * 16}}, _no_attachment)["status"] == "UNAVAILABLE"
    for url in ("http://example.org:8791", "https://127.0.0.1:8791"):
        monkeypatch.setenv("NEXUS_PV_ARCHIVE_URL", url)
        assert A.list_archive_agreements()["status"] == "UNAVAILABLE", url
    for bad in (None, [], "x", {}, {"old": {}, "new": {}}):
        assert A.compare_request(bad, _no_attachment)["status"] in {"INVALID", "UNAVAILABLE"}


def test_same_text_twice_and_unknown_ids_are_refused(archive) -> None:
    same = A.compare_request({"old": {"id": "a" * 16}, "new": {"id": "a" * 16}}, _no_attachment)
    assert same["status"] == "INVALID" and "différents" in same["message"]
    unknown = A.compare_request({"old": {"id": "a" * 16}, "new": {"id": "e" * 16}}, _no_attachment)
    assert unknown["status"] == "INVALID"
    assert A.compare_request({"old": {"id": "../etc/passwd"}, "new": {"id": "b" * 16}}, _no_attachment)["status"] == "INVALID"


def test_unreadable_import_is_reported_not_raised(archive) -> None:
    def broken(_attachment):
        raise ValueError("Le fichier importé est vide ou illisible.")

    result = A.compare_request({"old": {"id": "a" * 16}, "new": {"attachment": {"name": "x.txt"}}}, broken)
    assert result["status"] == "INVALID" and "illisible" in result["message"]


# --- routes HTTP du vrai serveur Nexus -----------------------------------------------------------------


@pytest.fixture
def nexus_http():
    server = _load("nexus_compare_server_under_test", "server.py")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.NexusHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def _post(base: str, path: str, payload):
    request = urllib.request.Request(base + path, data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def test_http_list_and_compare_routes(archive, nexus_http) -> None:
    with urllib.request.urlopen(nexus_http + "/api/agreements/list", timeout=30) as response:
        listing = json.loads(response.read())
    assert listing["ok"] is True and listing["status"] == "READY" and len(listing["documents"]) == 4

    code, body = _post(nexus_http, "/api/agreements/compare", {"old": {"id": "a" * 16}, "new": {"id": "b" * 16}})
    assert code == 200 and body["comparison"]["status"] == "READY" and body["comparison"]["resume"]["modifies"] == 2


def test_ids_from_the_list_survive_the_server_output_filter(archive, nexus_http) -> None:
    """Le serveur masque les hash de 32 caractères ou plus dans ses réponses : les références doivent rester utilisables."""
    import re

    with urllib.request.urlopen(nexus_http + "/api/agreements/list", timeout=30) as response:
        raw = response.read().decode("utf-8")
    listing = json.loads(raw)
    ids = [d["id"] for d in listing["documents"]]
    assert ids and all(re.fullmatch(r"[0-9a-f]{16}", i) for i in ids)
    assert not re.search(r"[0-9a-f]{32}", raw)
    by_title = {d["titre"] + d["date"]: d["id"] for d in listing["documents"]}
    code, body = _post(nexus_http, "/api/agreements/compare",
                       {"old": {"id": by_title["Accord télétravail2022-02-14"]}, "new": {"id": by_title["Accord télétravail2025-01-01"]}})
    assert code == 200 and body["comparison"]["status"] == "READY", body["comparison"]


def test_http_compare_with_an_uploaded_text_file(archive, nexus_http) -> None:
    attachment = {"name": "projet-avenant.txt", "mime_type": "text/plain", "content_base64": base64.b64encode(AVENANT.encode("utf-8")).decode()}
    code, body = _post(nexus_http, "/api/agreements/compare", {"old": {"id": "a" * 16}, "new": {"attachment": attachment}})
    comparison = body["comparison"]
    assert code == 200 and comparison["status"] == "READY" and comparison["mode"] == "avenant"
    assert comparison["modifications"][0]["valeurs"] == ["jour : 2 → 3"]


def test_http_compare_rejects_bad_files_and_is_disabled_by_default(monkeypatch, nexus_http) -> None:
    monkeypatch.delenv("NEXUS_ACCORDS_ARCHIVE_ENABLED", raising=False)
    code, body = _post(nexus_http, "/api/agreements/compare", {"old": {"id": "a" * 16}, "new": {"id": "b" * 16}})
    assert code == 200 and body["comparison"]["status"] == "DISABLED"
    monkeypatch.setenv("NEXUS_ACCORDS_ARCHIVE_ENABLED", "true")
    bad = {"name": "virus.exe", "content_base64": base64.b64encode(b"MZ").decode()}
    code, body = _post(nexus_http, "/api/agreements/compare", {"old": {"id": "a" * 16}, "new": {"attachment": bad}})
    assert code == 200 and body["comparison"]["status"] == "INVALID"
    code, _ = _post(nexus_http, "/api/agreements/compare", ["pas", "un", "objet"])
    assert code == 200  # corps non conforme : réponse INVALID, jamais d'erreur serveur
