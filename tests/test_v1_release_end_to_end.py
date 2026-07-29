from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "nexus-local-interface"


def _server_module():
    path = APP / "server.py"
    sys.path.insert(0, str(APP))
    spec = importlib.util.spec_from_file_location("nexus_release_e2e_server", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCENARIOS = (
    (
        "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE",
        "Le salarié reconnaît un retard mais conteste la gravité du grief avant son entretien.",
    ),
    (
        "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE",
        "Le salarié conteste les faits reprochés dans sa convocation disciplinaire.",
    ),
    (
        "QUESTION_SALARIE",
        "La direction veut imposer un passage d'un horaire de jour à un horaire posté.",
    ),
    (
        "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE",
        "Une procédure chimique interne ancienne est évoquée mais le document applicable manque.",
    ),
    (
        "QUESTION_SALARIE",
        "Un élu évoque des heures CSSCT sans préciser le mandat, la date ni la décision concernée.",
    ),
    (
        "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE",
        "Des données de badgeage sont utilisées pour reprocher des pauses à un salarié.",
    ),
    (
        "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE",
        "Un équipement de protection était indisponible pendant une opération présentant un risque chimique.",
    ),
    (
        "QUESTION_SALARIE",
        "Le salarié demande comment préparer une demande écrite alors qu'aucune source officielle pertinente n'est disponible.",
    ),
)


def test_eight_supported_paths_produce_safe_actionable_responses() -> None:
    server = _server_module()
    previous = None
    for employee_path, query in SCENARIOS:
        payload = server.analyze_public_question(query, 6, employee_path)
        encoded = json.dumps(payload, ensure_ascii=False)
        assert payload["ok"] is True
        assert payload["nexus_version"] == "1.0.0"
        assert payload["answer"]["route"]["employee_path"] == employee_path
        assert payload["public_summary"]["situation"]
        assert payload["public_summary"]["priority_questions"]
        assert payload["detailed_analysis"]
        assert payload["analysis_report"]["export_scope"] == "PUBLIC_SUMMARY_ONLY"
        assert payload["analysis_report"]["nexus_version"] == "1.0.0"
        assert "Traceback" not in encoded
        assert "C:\\Users\\" not in encoded
        assert len(encoded.encode("utf-8")) < 45_000
        if previous is not None:
            assert query not in previous
        previous = encoded


def test_interface_controls_cover_the_real_user_journey() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    script = (APP / "app.js").read_text(encoding="utf-8")
    for control in (
        "QUESTION_SALARIE",
        "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE",
        'id="copyReportButton"',
        'id="printReportButton"',
        'id="downloadReportButton"',
        'id="newAnalysisButton"',
    ):
        assert control in html
    assert 'document.createElement("details")' in script
    assert "window.print()" in script
    assert "summaryReportMarkdown(report)" in script
