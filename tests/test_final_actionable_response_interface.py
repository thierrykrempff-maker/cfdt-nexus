from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps" / "nexus-local-interface" / "app.js").read_text(
    encoding="utf-8"
)
STYLES = (ROOT / "apps" / "nexus-local-interface" / "styles.css").read_text(
    encoding="utf-8"
)


def test_interface_renders_summary_before_native_collapsible_details() -> None:
    assert "payload.public_summary" in APP
    assert 'document.createElement("details")' in APP
    assert 'document.createElement("summary")' in APP
    assert "Afficher l’analyse détaillée" in APP
    assert "report.details" not in APP


def test_copy_and_download_use_summary_markdown_only() -> None:
    assert "currentReportMarkdown = summaryReportMarkdown(report)" in APP
    assert "PUBLIC_SUMMARY_ONLY" not in APP
    assert "Cette partie complète la synthèse" in APP


def test_details_are_accessible_responsive_and_excluded_from_print() -> None:
    assert ".report-details > summary:focus-visible" in STYLES
    assert "@media print" in STYLES
    assert ".report-details { display: none !important; }" in STYLES
