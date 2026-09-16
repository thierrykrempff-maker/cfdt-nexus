from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from tests.cse_cssct_test_support import corpus


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "apps" / "nexus-local-interface" / "cse_agenda_analysis.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("nexus_cse_agenda_analysis", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def agenda_document() -> dict[str, object]:
    return {
        "name": "ordre-du-jour-cse.txt",
        "text": "",
        "passages": [
            {
                "reference": "Page 1",
                "text": (
                    "Ordre du jour\n"
                    "1. Réorganisation du laboratoire et évolution des effectifs\n"
                    "2. Calendrier prévisionnel des formations professionnelles"
                ),
            }
        ],
    }


def test_agenda_is_analyzed_point_by_point_against_previous_minutes(tmp_path) -> None:
    result = MODULE.build_cse_agenda_analysis(
        [agenda_document()], processed_root=corpus(tmp_path)
    )

    assert result["status"] == "READY"
    assert result["agenda_point_count"] == 2
    assert result["points_with_previous_minutes"] == 1
    first, second = result["points"]
    assert first["previously_discussed"] is True
    assert "réorganisation du laboratoire" in first["previous_minutes"][0]["excerpt"].lower()
    assert "contexte historique" in first["previous_minutes"][0]["limits"][0]
    assert first["questions_for_management"]
    assert second["previously_discussed"] is False


def test_agenda_analysis_requires_an_uploaded_agenda() -> None:
    result = MODULE.build_cse_agenda_analysis([])

    assert result == {
        "status": "AGENDA_REQUIRED",
        "message": "Ajoutez l’ordre du jour pour lancer l’analyse point par point.",
        "points": [],
    }


def test_only_selected_agenda_points_are_developed(tmp_path) -> None:
    result = MODULE.build_cse_agenda_analysis(
        [agenda_document()],
        processed_root=corpus(tmp_path),
        selected_positions=["2"],
    )

    assert result["status"] == "READY"
    assert result["agenda_point_count"] == 1
    assert result["points"][0]["position"] == "2"
    assert result["points"][0]["title"] == "Calendrier prévisionnel des formations professionnelles"
    assert result["points"][0]["questions_for_management"]


def test_empty_agenda_selection_is_rejected(tmp_path) -> None:
    result = MODULE.build_cse_agenda_analysis(
        [agenda_document()], processed_root=corpus(tmp_path), selected_positions=[]
    )

    assert result["status"] == "AGENDA_SELECTION_REQUIRED"
    assert result["points"] == []


def test_user_provided_previous_minutes_are_compared_without_persistence(tmp_path) -> None:
    previous_minutes = {
        "name": "PV-CSE-janvier-2025.txt",
        "passages": [
            {
                "reference": "Page 4",
                "text": (
                    "Le CSE examine le calendrier prévisionnel des formations "
                    "professionnelles. La direction transmettra un tableau de suivi."
                ),
            }
        ],
    }

    result = MODULE.build_cse_agenda_analysis(
        [agenda_document()],
        processed_root=tmp_path / "absent",
        selected_positions=["2"],
        additional_minutes_documents=[previous_minutes],
    )

    point = result["points"][0]
    assert result["uploaded_previous_minutes_count"] == 1
    assert point["previously_discussed"] is True
    assert point["previous_minutes"][0]["origin"] == "UPLOADED_MINUTES"
    assert point["previous_minutes"][0]["title"] == "PV-CSE-janvier-2025.txt"
    assert "norme juridique" in " ".join(point["previous_minutes"][0]["limits"])


def test_agenda_projection_contains_no_technical_or_local_identifiers(tmp_path) -> None:
    result = MODULE.build_cse_agenda_analysis(
        [agenda_document()], processed_root=corpus(tmp_path)
    )
    public_text = str(result).lower()

    for forbidden in (
        "chunk_id",
        "document_id",
        "query_id",
        "issue_id",
        "target_id",
        "storage_id",
        str(tmp_path).lower(),
    ):
        assert forbidden not in public_text


def test_agenda_extraction_is_bounded_and_ignores_the_header() -> None:
    document = {
        "name": "odj.txt",
        "passages": [
            {
                "reference": "Page 1",
                "text": "Ordre du jour\n" + "\n".join(
                    f"{index}. Question suffisamment détaillée numéro {index}"
                    for index in range(1, MODULE.MAX_AGENDA_POINTS + 10)
                ),
            }
        ],
    }

    points = MODULE.extract_agenda_points(document)

    assert len(points) == MODULE.MAX_AGENDA_POINTS
    assert all(point["title"] != "Ordre du jour" for point in points)


def test_preamble_is_not_mistaken_for_points_and_member_questions_are_kept() -> None:
    document = {
        "name": "ordre-du-jour-cse.txt",
        "passages": [
            {
                "reference": "Page 1",
                "text": (
                    "COMITÉ SOCIAL ET ÉCONOMIQUE\n"
                    "Réunion ordinaire du 12 mars 2026\n"
                    "Salle de conférence - 9 heures\n"
                    "Direction et délégation syndicale\n"
                    "13 Questions des membres du CSE\n"
                    "- Quel est le calendrier de remplacement du salarié absent ?\n"
                    "- Quels documents seront remis aux élus avant la consultation ?\n"
                    "14. Consultation sur la réorganisation du service"
                ),
            }
        ],
    }

    points = MODULE.extract_agenda_points(document)

    assert [point["position"] for point in points] == ["13", "13.1", "13.2", "14"]
    assert points[0]["title"] == "Questions des membres du CSE"
    assert "calendrier de remplacement" in points[1]["title"]
    assert "documents seront remis" in points[2]["title"]
    assert all("Réunion ordinaire" not in point["title"] for point in points)
    assert all("Salle de conférence" not in point["title"] for point in points)


def test_direction_section_and_member_questions_are_both_preserved() -> None:
    document = {
        "name": "ordre-du-jour-cse.pdf",
        "passages": [
            {
                "reference": "Page 1",
                "text": (
                    "Réunion ordinaire du 25 juin 2026\n"
                    "Points mis à l'ordre du jour par la Direction :\n"
                    "Situation économique et marche prévisionnelle des installations\n"
                    "Mise à jour du projet de réorganisation du laboratoire\n"
                    "Points mis à l'ordre du jour par les organisations syndicales :\n"
                    "1. Point sur le prix de l'énergie\n"
                    "2. Questions des membres du CSE"
                ),
            }
        ],
    }

    points = MODULE.extract_agenda_points(document)

    assert [point["position"] for point in points] == ["D1", "D2", "1", "2"]
    assert points[0]["display_label"] == "Direction — point 1"
    assert points[1]["title"] == "Mise à jour du projet de réorganisation du laboratoire"
    assert points[2]["display_label"] == "Point 1"


def test_interface_and_server_expose_only_the_cse_specific_projection() -> None:
    server = (ROOT / "apps" / "nexus-local-interface" / "server.py").read_text(
        encoding="utf-8"
    )
    javascript = (ROOT / "apps" / "nexus-local-interface" / "app.js").read_text(
        encoding="utf-8"
    )
    html = (ROOT / "apps" / "nexus-local-interface" / "index.html").read_text(
        encoding="utf-8"
    )

    assert 'portal_context.get("workspace") == "cse"' in server
    assert 'result["cse_agenda_analysis"]' in server
    assert '"/api/cse/agenda-preview"' in server
    assert "renderCseAgendaAnalysis(payload.cse_agenda_analysis || null)" in javascript
    assert "Questions pertinentes à poser à la direction" in javascript
    assert "Vérifier les points et les anciens PV" in html
    assert "Choisissez les points à approfondir" in html
    assert 'id="csePreviousPvDocuments"' in html
    assert "Ajouter les anciens PV à comparer" in html
    assert "selectedCseAgendaPoints" in javascript
    assert "Deux blocs distincts" in html
    assert "Points mis à l’ordre du jour par la Direction" in javascript
    assert "Questions des membres et organisations syndicales" in javascript
    assert "cse-agenda-group" in javascript
    assert "cse_selected_agenda_positions" in javascript
    assert "cse_previous_pv_attachments" in javascript
    assert 'currentWorkspace === "cse") return [2]' in javascript
    assert '? "ordre-du-jour"' in javascript
    assert "Analyser l’ordre du jour" in javascript
    assert "Importer un ordre du jour" in html
