"""Bloc « Sources officielles » : mots-clés, garde-fous, sections indépendantes.

Aucun appel réseau : les connecteurs et le service d'archive sont remplacés par des réponses FICTIVES.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pytest


APP_DIR = Path(__file__).resolve().parents[1] / "apps" / "nexus-local-interface"
sys.path.insert(0, str(APP_DIR))

import official_sources_search as module  # noqa: E402


@pytest.fixture(autouse=True)
def _flags(monkeypatch):
    monkeypatch.setenv(module.ENABLED_VARIABLE, "true")


def test_desactive_par_defaut(monkeypatch):
    monkeypatch.delenv(module.ENABLED_VARIABLE)
    assert module.official_sources_status() == {"enabled": False}
    result = module.search_official_sources("repos quotidien de nuit")
    assert result["status"] == "DISABLED" and result["sections"] == {}


def test_mots_cles_sans_noms_propres_ni_nombres():
    words = module.keywords_for_sources(
        "Un salarié, Monsieur Dupont, demande le repos quotidien de 11 heures après le travail de nuit à Sarralbe."
    )
    assert "repos" in words and "quotidien" in words and "nuit" in words
    assert not {"dupont", "monsieur", "sarralbe", "11"} & set(words)
    assert len(words) <= module.MAX_KEYWORDS


def test_mot_capitalise_en_debut_de_phrase_est_conserve():
    assert "licenciement" in module.keywords_for_sources("Licenciement pour insuffisance professionnelle")


def test_question_sans_mot_distinctif():
    assert module.search_official_sources("et le ?")["status"] == "EMPTY_QUERY"
    assert module.search_official_sources(None)["status"] == "EMPTY_QUERY"


def test_seuls_les_mots_cles_partent_vers_les_services(monkeypatch):
    seen = {}
    monkeypatch.setattr(module, "_legifrance_section", lambda q, *a: seen.setdefault("l", q) and {"status": "READY", "rows": [], "notice": ""})
    monkeypatch.setattr(module, "_judilibre_section", lambda q, *a: seen.setdefault("j", q) and {"status": "READY", "rows": [], "notice": ""})
    monkeypatch.setattr(module, "_ccn_section", lambda k, **kw: {"status": "READY", "rows": [], "notice": ""})
    monkeypatch.setattr(module, "search_extra_sources", lambda q: {"status": "READY", "rows": [], "notice": ""})
    monkeypatch.setattr(module, "_reference_section", lambda t, *a: {"status": "READY", "rows": [], "notice": ""})
    question = "Pierre Martin, matricule 4412, conteste son licenciement pour insuffisance professionnelle."
    result = module.search_official_sources(question)
    assert result["status"] == "READY"
    for sent in seen.values():
        assert "martin" not in sent.lower() and "4412" not in sent
        assert "pierre" not in sent.lower()
        assert set(sent.split()) <= set(result["keywords"]) | set(module.matching_topics(question)[0]["terms"])
    assert "Martin" not in " ".join(result["keywords"]) and "4412" not in " ".join(result["keywords"])


def test_une_section_en_panne_ne_bloque_pas_les_autres(monkeypatch):
    def boom(_query):
        raise RuntimeError("réseau coupé")

    monkeypatch.setattr(module, "_legifrance_section", boom)
    monkeypatch.setattr(module, "search_extra_sources", lambda q: {"status": "READY", "rows": [], "notice": ""})
    monkeypatch.setattr(module, "_reference_section", lambda t, *a: {"status": "READY", "rows": [], "notice": ""})
    monkeypatch.setattr(module, "_judilibre_section", lambda q, *a: {"status": "READY", "rows": [{"title": "x"}], "notice": ""})
    monkeypatch.setattr(module, "_ccn_section", lambda k, **kw: {"status": "UNAVAILABLE", "rows": [], "notice": "arrêté"})
    sections = module.search_official_sources("repos quotidien travail nuit")["sections"]
    assert sections["legifrance"]["status"] == "UNAVAILABLE"
    assert sections["judilibre"]["rows"] == [{"title": "x"}]
    assert sections["convention"]["status"] == "UNAVAILABLE"


def test_urls_limitees_aux_sites_officiels():
    assert module._safe_url("https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI1")
    assert module._safe_url("https://www.courdecassation.fr/decision/abc")
    assert module._safe_url("https://evil.example/legifrance.gouv.fr/") == ""
    assert module._safe_url("javascript:alert(1)") == ""


def test_convention_restreinte_au_document_ccnic(monkeypatch):
    monkeypatch.setattr(module, "_accords_enabled", lambda: True)
    monkeypatch.setattr(module, "_base_url", lambda: "http://127.0.0.1:1")
    monkeypatch.setattr(module, "_archive_endpoint", lambda: "http://127.0.0.1:1/api/passages")
    monkeypatch.setattr(
        module,
        "_service_call",
        lambda url, body=None: {
            "documents": [
                {"id": "a" * 16, "fichier": "2014.12.17_Accord Mutuelle.pdf"},
                {"id": "b" * 16, "fichier": "ccnic_septembre2013.pdf"},
            ]
        },
    )
    sent = {}

    def fake_post(endpoint, body):
        sent.update(body)
        return {"points": {"ccn": [{"fichier": "ccnic_septembre2013.pdf", "page": 7, "extrait": "Texte fictif sur le repos."}]}}

    monkeypatch.setattr(module, "_service_post", fake_post)
    section = module._ccn_section(["repos", "quotidien"])
    assert sent["include"] == ["b" * 16] and sent["corpus"] == "accords"
    assert section["status"] == "READY" and section["rows"][0]["title"] == module.CCN_TITLE
    assert "2013" in section["notice"]


def test_convention_non_indexee(monkeypatch):
    monkeypatch.setattr(module, "_accords_enabled", lambda: True)
    monkeypatch.setattr(module, "_base_url", lambda: "http://127.0.0.1:1")
    monkeypatch.setattr(module, "_archive_endpoint", lambda: "http://127.0.0.1:1/api/passages")
    monkeypatch.setattr(module, "_service_call", lambda url, body=None: {"documents": [{"id": "a" * 16, "fichier": "autre.pdf"}]})
    assert module._ccn_section(["repos"])["status"] == "NOT_INDEXED"


def test_service_arrete(monkeypatch):
    monkeypatch.setattr(module, "_accords_enabled", lambda: True)
    monkeypatch.setattr(module, "_base_url", lambda: "http://127.0.0.1:1")
    monkeypatch.setattr(module, "_archive_endpoint", lambda: "http://127.0.0.1:1/api/passages")
    monkeypatch.setattr(module, "_service_call", lambda url, body=None: None)
    assert module._ccn_section(["repos"])["status"] == "UNAVAILABLE"


def test_sujets_reconnus_et_articles_de_reference():
    keys = [t["key"] for t in module.matching_topics("Quelles sont les conditions du licenciement économique ?")]
    assert keys[0] == "licenciement_economique"
    keys = [t["key"] for t in module.matching_topics("Un salarié est licencié pour insuffisance professionnelle")]
    assert keys[0] == "licenciement_personnel" and "licenciement_economique" not in keys
    assert module.matching_topics("Où est la salle de réunion ?") == []


def test_table_des_sujets_bien_formee():
    from official_topics import TOPICS
    import re as _re

    keys = [t["key"] for t in TOPICS]
    assert len(keys) == len(set(keys))
    for topic in TOPICS:
        assert topic["when"] and all(topic["when"]) and topic["terms"]
        assert all(_re.fullmatch(r"L\d{4}-\d+(-\d+)?", article) for article in topic["articles"]), topic["key"]


def test_articles_de_reference_sans_doublon_ni_depassement(monkeypatch):
    fetched = []

    class FakeClient:
        config = type("C", (), {"configured": True})()

    def fake_fetch(client, article, label, full_text=False):
        fetched.append(article)
        return {"title": article, "excerpt": "x", "url": "", "article": article}

    class FakeModule:
        LegifranceClient = FakeClient

    monkeypatch.setattr(module, "_connector_modules", lambda: (FakeModule, None))
    monkeypatch.setattr(module, "_fetch_article", fake_fetch)
    topics = module.matching_topics("licenciement économique et sanction disciplinaire")
    section = module._reference_section(topics)
    assert section["status"] == "READY"
    assert len(fetched) == len(set(fetched)) <= module.MAX_REFERENCE_ARTICLES


def test_mots_parasites_retires():
    words = module.keywords_for_sources("Un salarié vient d'être licencié pour insuffisance professionnelle, a-t-on déjà vu ça ?")
    assert "vient" not in words and "deja" not in words and "insuffisance" in words


def test_prenom_en_debut_de_phrase_retire():
    assert "pierre" not in module.keywords_for_sources("Pierre Martin conteste son licenciement")
    assert "monsieur" not in module.keywords_for_sources("Monsieur Dupont conteste son licenciement")
    assert "licenciement" in module.keywords_for_sources("Licenciement abusif ?")
