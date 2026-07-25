from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "nexus-local-interface"


def test_progressive_form_contains_five_steps_and_response_modes() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    for step in range(1, 6):
        assert f'data-step="{step}"' in html
    for mode in ("QUICK", "CASE", "EXPERT"):
        assert f'value="{mode}"' in html
    assert 'value="CASE" checked' in html


def test_each_business_space_has_expected_choices() -> None:
    js = (APP / "app.js").read_text(encoding="utf-8")
    for choice in (
        "Changement de poste",
        "Discipline",
        "Préparer une réunion",
        "Réorganisation",
        "Rechercher une clause",
        "Préparer des revendications",
        "Heures supplémentaires",
        "Astreinte",
        "IJSS",
    ):
        assert choice in js


def test_form_builds_explicit_structured_context() -> None:
    js = (APP / "app.js").read_text(encoding="utf-8")
    for key in (
        "workspace",
        "situation_type",
        "user_question",
        "facts",
        "available_documents",
        "period",
        "urgency",
        "desired_outcome",
        "response_mode",
        "allowed_engines",
        "confidentiality",
    ):
        assert f"{key}:" in js
    assert "buildStructuredRequest()" in js
