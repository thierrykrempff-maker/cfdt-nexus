"""Dossier « Nexus → Claude » : structure, numérotation des sources, garde-fous.

Sources et archives FICTIVES : aucun appel réseau, aucun vrai document.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

import pytest


APP_DIR = Path(__file__).resolve().parents[1] / "apps" / "nexus-local-interface"
sys.path.insert(0, str(APP_DIR))

import claude_dossier as module  # noqa: E402


def _official(**sections):
    base = {"reference": {"status": "READY", "rows": []}, "legifrance": {"status": "READY", "rows": []},
            "judilibre": {"status": "READY", "rows": []}, "convention": {"status": "READY", "rows": []}}
    base.update(sections)
    return {"status": "READY", "keywords": ["licenciement"], "topics": [], "sections": base}


@pytest.fixture
def fake(monkeypatch):
    calls = {}

    def fake_official(question, *, full_text=False):
        calls["full_text"] = full_text
        return _official(
            reference={"status": "READY", "rows": [{"title": "Code du travail, article L1232-1", "detail": "En vigueur",
                                                    "excerpt": "court", "full_text": "Texte intégral fictif.", "url": "https://www.legifrance.gouv.fr/x"}]},
            judilibre={"status": "READY", "rows": [{"title": "Cour de cassation 2011", "detail": "Solution : cassation",
                                                    "excerpt": "Résumé fictif.", "url": ""}]},
            convention={"status": "READY", "rows": [{"title": "CCN", "detail": "p. 3", "excerpt": "Passage CCN fictif."}]},
            autres={"status": "READY", "rows": [{"title": "Guide fictif", "detail": "DREETS Grand Est", "excerpt": "Guide DREETS fictif.", "url": ""}]},
        )

    def fake_archive(corpus, query, **kwargs):
        calls.setdefault("archive", []).append((corpus, query, kwargs.get("strict")))
        row = {"title": f"{corpus} fictif", "date": "2016-11-15", "instance": "CE", "reference": "p. 1", "excerpt": f"Extrait {corpus}."}
        return {"status": "READY", "results": [row]}

    monkeypatch.setattr(module, "search_official_sources", fake_official)
    monkeypatch.setattr(module, "search_archive", fake_archive)
    return calls


def test_question_vide():
    assert module.build_claude_dossier("  ")["status"] == "EMPTY_QUERY"
    assert module.build_claude_dossier(None)["markdown"] == ""


def test_dossier_complet_et_numerote(fake):
    result = module.build_claude_dossier("Un salarié licencié pour insuffisance professionnelle ?")
    markdown = result["markdown"]
    assert result["status"] == "READY" and fake["full_text"] is True
    numbers = [int(n) for n in re.findall(r"^\*\*\[S(\d+)\]", markdown, flags=re.M)]
    assert numbers == list(range(1, len(numbers) + 1)) and result["sources"] == len(numbers) == 6
    for marker in ("## Consigne", "## Question", "Texte intégral fictif.", "Résumé fictif.", "Passage CCN fictif.",
                   "Extrait accords.", "Extrait pv.", "Guide DREETS fictif.", "## Limites de la recherche", "uniquement"):
        assert marker in markdown
    assert result["counts"] == {"loi": 1, "jurisprudence": 1, "convention": 1, "accords": 1, "pv": 1, "autres": 1}


def test_texte_integral_prefere_a_l_extrait(fake):
    markdown = module.build_claude_dossier("licenciement")["markdown"]
    assert "Texte intégral fictif." in markdown and "court" not in markdown


def test_requete_archive_precise_d_abord(fake):
    module.build_claude_dossier("Licenciement pour insuffisance professionnelle")
    assert fake["archive"][0][2] is True  # tous les mots ensemble avant tout repli


def test_source_indisponible_signalee(monkeypatch, fake):
    monkeypatch.setattr(module, "search_archive", lambda corpus, query, **kw: {"status": "UNAVAILABLE", "results": []})
    markdown = module.build_claude_dossier("licenciement économique")["markdown"]
    assert "source non consultée (UNAVAILABLE)" in markdown and "Aucun PV retrouvé." in markdown


def test_convention_pas_dans_les_accords(monkeypatch, fake):
    def archive(corpus, query, **kw):
        rows = [{"title": "ccnic_septembre2013", "excerpt": "doublon CCN"}, {"title": "Accord CET", "excerpt": "vrai accord"}]
        return {"status": "READY", "results": rows if corpus == "accords" else []}

    monkeypatch.setattr(module, "search_archive", archive)
    markdown = module.build_claude_dossier("compte épargne temps")["markdown"]
    assert "vrai accord" in markdown and "doublon CCN" not in markdown


def test_ligne_de_commande_sans_argument(capsys):
    assert module.main([]) == 2
