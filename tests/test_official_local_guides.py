"""Guides PDF de la DREETS lus en texte intégral : recherche par mots rares, tables des matières écartées. Cache FICTIF, aucun réseau."""

from __future__ import annotations

from pathlib import Path
import sys

APP_DIR = Path(__file__).resolve().parents[1] / "apps" / "nexus-local-interface"
sys.path.insert(0, str(APP_DIR))

import official_extra_sources as extra  # noqa: E402
import official_local_guides as module  # noqa: E402

FAKE = {"id": "fake", "title": "Guide fictif", "pdf": module.HOST + "x.pdf", "page": module.HOST + "guide"}


def _install(monkeypatch, pages):
    monkeypatch.setattr(module, "GUIDES", (FAKE,))
    monkeypatch.setattr(module, "_MEMORY", {"fake": {"id": "fake", "pages": pages}})


def test_passage_rare_trouve(monkeypatch):
    _install(monkeypatch, ["Introduction generale sur les jours de repos.",
                           "Le Vendredi saint et le 26 decembre sont des jours feries propres a la Moselle pour les salaries."])
    rows = module.search_guides(extra._stems("jours fériés Moselle Vendredi saint"), extra._enough_text)
    assert len(rows) == 1 and "(p. 2)" in rows[0]["title"] and "Vendredi saint" in rows[0]["excerpt"]
    assert rows[0]["url"] == module.HOST + "guide"


def test_table_des_matieres_ecartee(monkeypatch):
    toc = "Sommaire jours feries Moselle Vendredi saint ........ 3 ........ 4 ........ 5 ........ 6"
    _install(monkeypatch, [toc, "Le Vendredi saint est un jour ferie en Moselle."])
    rows = module.search_guides(extra._stems("jours fériés Moselle Vendredi saint"), extra._enough_text)
    assert rows and "(p. 2)" in rows[0]["title"]


def test_mot_banal_seul_ne_suffit_pas(monkeypatch):
    _install(monkeypatch, ["Les jours ouvrables et les jours calendaires se comptent differemment."])
    assert module.search_guides(extra._stems("jours fériés Moselle Vendredi saint"), extra._enough_text) == []


def test_aucun_guide_en_cache_ne_leve_pas(monkeypatch, tmp_path):
    monkeypatch.setattr(module, "GUIDES", (FAKE,))
    monkeypatch.setattr(module, "_MEMORY", {})
    monkeypatch.setattr(module, "CACHE_DIR", tmp_path / "vide")
    monkeypatch.setattr(module, "_background_fetch", lambda guide: None)
    assert module.search_guides(extra._stems("heures supplémentaires"), extra._enough_text) == []


def test_telechargement_limite_a_l_hote_dreets():
    assert module._download({"id": "x", "pdf": "https://evil.example/a.pdf"}) is None
    assert all(guide["pdf"].startswith(module.HOST) for guide in module.GUIDES)
