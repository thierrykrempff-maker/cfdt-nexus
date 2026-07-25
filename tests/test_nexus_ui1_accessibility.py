from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "nexus-local-interface"


def test_page_has_landmarks_skip_link_and_heading_hierarchy() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    assert 'class="skip-link"' in html
    assert "<header" in html and "<main" in html
    assert re.search(r"<h1[^>]*>", html)
    assert 'lang="fr"' in html


def test_controls_have_labels_and_live_error_regions() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    assert 'for="questionInput"' in html
    assert 'id="wizardError" role="alert"' in html
    assert 'aria-live="polite"' in html
    assert 'aria-expanded="false"' in html


def test_keyboard_focus_and_reduced_motion_are_supported() -> None:
    css = (APP / "styles.css").read_text(encoding="utf-8")
    assert ":focus-visible" in css
    assert "outline: 3px solid" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
