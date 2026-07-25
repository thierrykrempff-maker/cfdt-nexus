from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "nexus-local-interface"


def test_required_ui_scenarios_have_direct_controls_or_states() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    js = (APP / "app.js").read_text(encoding="utf-8")
    required = (
        "horaires", "discipline", "maladie", "reunion", "reorganisation", "avis",
        "ancien-pv", "rechercher-clause", "revendications", "heures-supplementaires",
        "astreinte", "QUICK", "CASE", "EXPERT",
    )
    joined = f"{html}\n{js}"
    for scenario in required:
        assert scenario in joined


def test_partial_result_privacy_and_disabled_modes_are_user_facing() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    js = (APP / "app.js").read_text(encoding="utf-8")
    assert "Analyse avancée non activée" in html
    assert "Le contrôle avancé n’est pas activé" in html
    assert "Analyse impossible" in js
    assert "Confidentialité" in html


def test_result_actions_cover_edit_document_draft_home_and_restart() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    for label in ("Modifier les informations", "Ajouter un document", "Générer un brouillon", "Revenir à l’accueil", "Nouvelle analyse"):
        assert label in html
