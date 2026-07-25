from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "nexus-local-interface"


def test_portal_warns_against_sensitive_inputs() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    for forbidden_input in ("NIR", "coordonnées bancaires", "diagnostic médical", "mot de passe"):
        assert forbidden_input in html
    assert "aucune sauvegarde automatique" in html.lower()
    assert "Aucun" in html and "Envoi externe" in html


def test_frontend_does_not_persist_or_log_user_content() -> None:
    js = (APP / "app.js").read_text(encoding="utf-8")
    for forbidden in ("localStorage", "sessionStorage", "console.log", "indexedDB"):
        assert forbidden not in js
    assert "source.chunk_id" not in js


def test_content_security_policy_blocks_external_resources() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    assert "default-src 'self'" in html
    assert "connect-src 'self'" in html
    assert "object-src 'none'" in html
