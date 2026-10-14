"""Autres sources officielles (CDTN, service-public, CNIL, DREETS, CARSAT, INRS) : réponses FICTIVES, aucun réseau."""

from __future__ import annotations

from pathlib import Path
import sys

APP_DIR = Path(__file__).resolve().parents[1] / "apps" / "nexus-local-interface"
sys.path.insert(0, str(APP_DIR))

import official_extra_sources as module  # noqa: E402


class _Client:
    def __init__(self, payload=None, error=None):
        self.payload, self.error = payload, error

    def search_sources(self, query, limit=2):
        if self.error:
            raise self.error
        return self.payload


def test_site_en_panne_ne_bloque_pas_les_autres(monkeypatch):
    def load(module_name, cls):
        if module_name == "cnil_connector":
            return _Client(error=RuntimeError("réseau"))
        return _Client({"sources": [{"document": f"Page {module_name}", "url": "https://evil.example/x", "excerpt": "Texte fictif."}]})

    monkeypatch.setattr(module, "_load", load)
    section = module.search_extra_sources("licenciement")
    assert section["status"] == "READY" and len(section["rows"]) == len(module.CONNECTORS) - 1
    assert "CNIL" in section["notice"] and "Non consultés" in section["notice"]


def test_liens_limites_aux_sites_de_la_source(monkeypatch):
    payload = {"sources": [
        {"document": "Bonne", "url": "https://www.cnil.fr/fr/page", "excerpt": "x"},
        {"document": "Mauvaise", "url": "https://evil.example/cnil", "excerpt": "y"},
    ]}
    monkeypatch.setattr(module, "_load", lambda m, c: _Client(payload))
    row_ok, row_bad = module._one("cnil", "cnil_connector", "CnilClient", "CNIL", ("https://www.cnil.fr/",), "q")["rows"]
    assert row_ok["url"].startswith("https://www.cnil.fr/") and row_bad["url"] == ""


def test_connecteur_sans_page_renvoie_une_liste_vide(monkeypatch):
    monkeypatch.setattr(module, "_load", lambda m, c: _Client({"available": False, "sources": []}))
    assert module._one("inrs", "inrs_connector", "InrsClient", "INRS", ("https://www.inrs.fr/",), "bruit")["rows"] == []


def test_fiche_identique_une_seule_fois(monkeypatch):
    payload = {"sources": [{"document": "Fiche", "url": "https://code.travail.gouv.fr/fiche", "excerpt": "x"}]}
    monkeypatch.setattr(module, "_load", lambda m, c: _Client(payload if m in ("cdtn_connector", "pratique_officielle_connector") else {"sources": []}))
    assert len(module.search_extra_sources("q")["rows"]) == 1
