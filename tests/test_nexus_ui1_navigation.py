from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "nexus-local-interface"


def test_business_cards_open_progressive_workspaces() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    js = (APP / "app.js").read_text(encoding="utf-8")
    for workspace in ("employee", "cse", "negotiation", "payroll"):
        assert f'data-open-workspace="{workspace}"' in html
        assert f"{workspace}:" in js
    assert "openWorkspace(button.dataset.openWorkspace" in js


def test_navigation_supports_home_edit_and_new_analysis() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    js = (APP / "app.js").read_text(encoding="utf-8")
    assert html.count("data-return-home") >= 3
    assert 'id="editInformationButton"' in html
    assert 'id="newAnalysisButton"' in html
    assert 'showOnly("home")' in js
    assert 'showOnly("wizard")' in js


def test_settings_are_read_only_and_do_not_mutate_feature_flags() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    js = (APP / "app.js").read_text(encoding="utf-8")
    assert 'id="settingsPanel"' in html
    assert "Les moteurs avancés ne sont jamais activés depuis cette interface." in html
    assert "localStorage" not in js
    assert "sessionStorage" not in js
