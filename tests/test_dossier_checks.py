"""Contrôles automatiques des extraits (provenance, lisibilité, pertinence, divergences) : données FICTIVES, aucun réseau."""

from __future__ import annotations

from pathlib import Path
import sys

APP_DIR = Path(__file__).resolve().parents[1] / "apps" / "nexus-local-interface"
sys.path.insert(0, str(APP_DIR))

import dossier_checks as module  # noqa: E402

GARBAGE = "Slllulllillelælslolelulols|ol-lolu|+lsiofwis|-l-|lol-fsinlols (she 7. TOTALE ET A tell lotilule tele te ler es li fes fe ler"
GOOD = "Lorsque l'employeur envisage de prendre une sanction, il convoque le salarié à un entretien préalable en précisant l'objet de la convocation."


def test_qualite_du_texte():
    assert module.text_quality(GOOD) > 0.9
    assert module.text_quality(GARBAGE) < module.MIN_QUALITY
    assert module.text_quality("Court.") == 1.0


def test_extrait_illisible_et_hors_sujet_ecartes():
    gathered = {"pv": [{"excerpt": GARBAGE}, {"excerpt": GOOD}, {"excerpt": "Le menu de la cantine pour la semaine prochaine est un plat chaud et un dessert."}],
                "accords": [], "docs": [], "extra": [], "convention": [], "reglement": []}
    report = module.check_rows(gathered, "sanction disciplinaire entretien préalable")
    assert [row["excerpt"] for row in gathered["pv"]] == [GOOD]
    assert report["pv"] == {"gardes": 1, "illisible": 1, "hors_sujet": 1}


def test_provenance_verifiee_ou_non_retrouvee(monkeypatch):
    document = {"texte": "Préambule. " + GOOD + " Suite du document."}
    monkeypatch.setattr(module, "_base_url", lambda: "http://127.0.0.1:1")

    def service(url, body=None):
        if "documents?corpus" in url:
            return {"documents": [{"id": "a" * 16, "fichier": "PV 2016/CR.pdf"}]}
        return document

    monkeypatch.setattr(module, "_service_call", service)
    cache = {}
    assert module.verify_provenance({"_source": "PV 2016/CR.pdf", "excerpt": "…" + GOOD + "…"}, "pv", cache) == "verifie"
    altered = GOOD.replace("sanction", "mesure inventée") + " Autre texte qui n'existe pas dans le document source."
    assert module.verify_provenance({"_source": "PV 2016/CR.pdf", "excerpt": altered}, "pv", cache) == "non_retrouve"
    assert module.verify_provenance({"excerpt": GOOD}, "pv", cache) == "non_controle"
    assert module.verify_provenance({"_source": "inconnu.pdf", "excerpt": GOOD}, "pv", cache) == "non_controle"


def test_service_arrete_donne_non_controle(monkeypatch):
    monkeypatch.setattr(module, "_base_url", lambda: None)
    assert module.verify_provenance({"_source": "x.pdf", "excerpt": GOOD}, "pv", {}) == "non_controle"


def test_divergences_entre_sources():
    rows = [("[S1]", "Le préavis est de 2 mois pour un salarié ayant plus de deux ans d'ancienneté."),
            ("[S2]", "En cas de licenciement, le préavis est de 3 mois pour les cadres."),
            ("[S3]", "Le délai de prévenance est de 15 jours."),
            ("[S4]", "Le délai de prévenance est de 15 jours aussi.")]
    lines = module.find_divergences(rows)
    assert any("préavis" in line.lower() or "preavis" in line.lower() for line in lines)
    assert any("2 mois selon [S1]" in line and "3 mois selon [S2]" in line for line in lines)
    assert not any("délai" in line.lower() or "delai" in line.lower() for line in lines)  # même valeur : pas de divergence
    assert module.find_divergences([("[S1]", "Aucun chiffre ici.")]) == []


def test_valeurs_en_pourcentage_et_en_euros_ne_plantent_pas():
    rows = [("[S1]", "La majoration est de 25 % pour les huit premières heures."),
            ("[S2]", "La majoration est de 50 % au-delà."),
            ("[S3]", "Le plafond de l'indemnité est de 2 500 € selon l'accord.")]
    lines = module.find_divergences(rows)
    assert any("majoration" in line and "25 % selon [S1]" in line and "50 % selon [S2]" in line for line in lines)
