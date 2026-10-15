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


TOPICS_FAKE = ("Licenciement pour insuffisance professionnelle, heures de nuit manquantes, compte épargne temps, "
               "sanction disciplinaire, mise à pied, formation, vidéosurveillance, travail de nuit.")


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
            reglement={"status": "READY", "rows": [{"title": "Règlement intérieur", "detail": "p. 7", "excerpt": "Échelle des sanctions fictive. " + TOPICS_FAKE}]},
            autres={"status": "READY", "rows": [{"title": "Guide fictif", "detail": "DREETS Grand Est", "excerpt": "Guide DREETS fictif. " + TOPICS_FAKE, "url": ""}]},
        )

    def fake_archive(corpus, query, **kwargs):
        calls.setdefault("archive", []).append((corpus, query, kwargs.get("strict")))
        row = {"title": f"{corpus} fictif", "date": "2016-11-15", "instance": "CE", "reference": "p. 1", "excerpt": f"Extrait {corpus}. {TOPICS_FAKE}"}
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
    assert numbers == list(range(1, len(numbers) + 1)) and result["sources"] == len(numbers) == 8
    for marker in ("## Consigne", "## Question", "Texte intégral fictif.", "Résumé fictif.", "Passage CCN fictif.",
                   "Extrait accords.", "Extrait pv.", "Extrait docs.", "Échelle des sanctions fictive.", "D bis. Règlement intérieur", "Guide DREETS fictif.", "## Limites de la recherche", "uniquement"):
        assert marker in markdown
    assert result["counts"] == {"loi": 1, "jurisprudence": 1, "convention": 1, "accords": 1, "pv": 1, "autres": 1, "documents": 1, "reglement_interieur": 1}


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
        rows = [{"title": "ccnic_septembre2013", "excerpt": "doublon CCN"}, {"title": "Accord CET", "excerpt": "vrai accord compte épargne temps"}]
        return {"status": "READY", "results": rows if corpus == "accords" else []}

    monkeypatch.setattr(module, "search_archive", archive)
    markdown = module.build_claude_dossier("compte épargne temps")["markdown"]
    assert "vrai accord" in markdown and "doublon CCN" not in markdown


def test_ligne_de_commande_sans_argument(capsys):
    assert module.main([]) == 2


def test_ordre_du_jour_point_par_point(fake):
    result = module.build_agenda_dossier(
        [{"position": "1", "title": "Projet de licenciement pour inaptitude"}, {"position": "2", "title": "Bilan de la formation"}, {"title": "  "}],
        "CSE du 16 octobre",
    )
    markdown = result["markdown"]
    assert result["status"] == "READY" and result["points"] == 2
    assert "## Point 1 — Projet de licenciement pour inaptitude" in markdown and "## Point 2 — Bilan de la formation" in markdown
    assert "CSE du 16 octobre" in markdown and "point par point" in markdown and "délégué syndical CFDT" in markdown
    numbers = [int(n) for n in re.findall(r"^\*\*\[S(\d+)\]", markdown, flags=re.M)]
    assert numbers == list(range(1, len(numbers) + 1)) == list(range(1, result["sources"] + 1))
    assert "déjà cité plus haut" in markdown  # la même source n'est numérotée qu'une fois


def test_ordre_du_jour_vide_ou_trop_long(fake):
    assert module.build_agenda_dossier([])["status"] == "EMPTY_QUERY"
    many = [{"title": f"Point {i}"} for i in range(40)]
    assert module.build_agenda_dossier(many)["points"] == module.MAX_AGENDA_POINTS


def test_defense_d_un_salarie(fake):
    result = module.build_claude_dossier("Licenciement pour insuffisance professionnelle", mode="defense",
                                         situation="Le salarié a 12 ans d'ancienneté, aucune sanction antérieure.")
    markdown = result["markdown"]
    assert "défense d'un salarié" in markdown and "## Situation du salarié" in markdown and "12 ans d'ancienneté" in markdown
    assert "délais de prescription" in markdown and "[S1]" in markdown


def test_mode_inconnu_retombe_sur_question(fake):
    assert "## Question" in module.build_claude_dossier("licenciement", mode="piratage")["markdown"]


def test_defense_la_recherche_part_du_type_et_de_la_description(monkeypatch, fake):
    seen = {}
    original = module.gather

    def spy(text, **kwargs):
        seen["text"] = text
        return original(text, **kwargs)

    monkeypatch.setattr(module, "gather", spy)
    result = module.build_claude_dossier("Mise à pied", mode="defense", topic_text="Trois retards en un mois",
                                         situation="- Date : 12 mars\n- Motif : retards répétés " + "x" * 50)
    assert seen["text"] == "Mise à pied Trois retards en un mois"
    assert "retards répétés" in result["markdown"] and "Date : 12 mars" in result["markdown"]


def test_defense_conserve_les_lignes_des_faits(fake):
    markdown = module.build_claude_dossier("Mise à pied", mode="defense", situation="Ligne un\n\n  - Ligne   deux  ")["markdown"]
    assert "Ligne un\n- Ligne deux" in markdown


def test_mode_paie_et_documents(fake):
    result = module.build_claude_dossier("Heures de nuit manquantes", mode="paie", situation="Bulletin de mars" + chr(10) + "- Heures de nuit : 24")
    markdown = result["markdown"]
    assert "contrôle de paie et de congés" in markdown and "## Situation de paie ou de congés à contrôler" in markdown
    assert "prescription" in markdown and "G. Documents syndicaux" in markdown and "Extrait docs." in markdown


def test_reglement_interieur_pas_repete_dans_les_accords(monkeypatch, fake):
    def archive(corpus, query, **kw):
        rows = [{"title": "Règlement intérieur", "excerpt": "doublon RI"}, {"title": "Accord CET", "excerpt": "vrai accord sanction disciplinaire"}]
        return {"status": "READY", "results": rows if corpus == "accords" else []}

    monkeypatch.setattr(module, "search_archive", archive)
    markdown = module.build_claude_dossier("sanction disciplinaire")["markdown"]
    assert "vrai accord" in markdown and "doublon RI" not in markdown and "Échelle des sanctions fictive." in markdown


def test_meme_fiche_relayee_par_deux_sites_numerotee_une_fois():
    numbering = module._Numbering()
    first = numbering.number({"title": "La procédure", "url": "https://code.travail.gouv.fr/fiche", "excerpt": "Après l'entretien, l'employeur attend deux jours."})
    second = numbering.number({"title": "La procédure", "url": "https://code.travail.gouv.fr/fiche#procedure", "excerpt": "Après l'entretien, l'employeur attend deux jours."})
    assert first == (1, False) and second == (1, True)
