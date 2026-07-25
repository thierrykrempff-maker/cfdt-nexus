from __future__ import annotations

from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sys
import threading
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "nexus-local-interface"
LOGO = APP / "assets" / "logo-cfdt-ineos-sarralbe.jpg"


def source(name: str) -> str:
    return (APP / name).read_text(encoding="utf-8")


def test_home_exposes_four_business_spaces_without_internal_lot_names() -> None:
    html = source("index.html")
    for label in ("Questions salariés", "CSE", "Négociations et accords", "Paie et rémunération"):
        assert label in html
    for internal_name in ("R1A", "R1B", "R1C", "R1D", "R1E", "R2A", "R2B", "R2C"):
        assert internal_name not in html


def test_home_exposes_secondary_tools_and_safe_empty_states() -> None:
    html = source("index.html")
    for label in ("Recherche documentaire", "Dossiers en cours", "Historique", "Outils et modèles"):
        assert label in html
    assert "Aucun dossier enregistré dans cette version" in html
    assert "aucune sauvegarde automatique" in html.lower()


def test_visual_identity_is_business_facing_and_responsive() -> None:
    css = source("styles.css")
    assert "--orange: #e85d04" in css
    assert ".workspace-grid" in css
    assert "@media (max-width: 1180px)" in css
    assert "@media (max-width: 580px)" in css


def test_local_cfdt_ineos_logo_is_declared_with_accessible_text() -> None:
    html = source("index.html")
    assert 'src="assets/logo-cfdt-ineos-sarralbe.jpg"' in html
    assert 'alt="Logo CFDT INEOS Sarralbe"' in html
    assert "data:image" not in html
    assert 'src="http://' not in html and 'src="https://' not in html


def test_logo_static_file_exists_and_keeps_its_jpeg_format() -> None:
    assert LOGO.is_file()
    assert LOGO.suffix.lower() == ".jpg"
    assert LOGO.stat().st_size > 1_000


def test_logo_css_preserves_proportions_and_is_responsive() -> None:
    css = source("styles.css")
    logo_block = css.split(".brand-logo {", 1)[1].split("}", 1)[0]
    assert "height: auto" in logo_block
    assert "max-width:" in logo_block
    assert "object-fit: contain" in logo_block
    assert "@media (max-width: 580px)" in css
    assert ".brand-logo" in css.split("@media (max-width: 580px)", 1)[1]


def load_server():
    server_path = APP / "server.py"
    sys.path.insert(0, str(APP))
    spec = importlib.util.spec_from_file_location("nexus_ui1_logo_server", server_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextmanager
def local_server():
    module = load_server()
    httpd = module.ThreadingHTTPServer(("127.0.0.1", 0), module.NexusHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def test_logo_is_served_locally_over_http() -> None:
    with local_server() as base:
        with urllib.request.urlopen(  # noqa: S310 - local server only.
            base + "/assets/logo-cfdt-ineos-sarralbe.jpg",
            timeout=10,
        ) as response:
            body = response.read()
            assert response.status == 200
            assert response.headers.get_content_type() == "image/jpeg"
    assert body == LOGO.read_bytes()
