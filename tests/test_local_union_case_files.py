from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "apps" / "nexus-local-interface" / "local_cases.py"


def load_module():
    spec = importlib.util.spec_from_file_location("local_union_cases", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_case() -> dict[str, object]:
    return {
        "title": "Changement d’horaires — laboratoire",
        "status": "OPEN",
        "question": "Le changement peut-il être refusé ?",
        "public_summary": {
            "summary": "La qualification dépend du contrat et du cycle proposé.",
            "technical_trace": {
                "query_id": "query-private",
                "fact_id": "fact-private",
            },
        },
        "follow_up_answers": [
            {
                "question": "Le cycle comporte-t-il des nuits ?",
                "answer": "Non, mais il comporte des week-ends et jours fériés.",
            }
        ],
        "documents": ["Projet d’avenant", "Planning projeté"],
        "uploaded_documents": [
            {
                "title": "projet-avenant.pdf",
                "format": "PDF",
                "page_count": 2,
                "truncated": False,
                "status": "LU_POUR_CETTE_ANALYSE",
            }
        ],
        "actions": ["Demander le projet écrit"],
        "notes": "Dossier pseudonymisé.",
        "final_decision": {},
    }


def test_reading_an_empty_store_never_creates_a_directory() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "cases"
        store = module.LocalCaseStore(root)
        assert store.list_cases() == []
        assert not root.exists()


def test_case_is_created_only_after_explicit_save_and_can_be_reloaded() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "cases"
        store = module.LocalCaseStore(root)
        saved = store.save_case(sample_case())

        assert root.is_dir()
        assert saved["case_ref"].startswith("DOSSIER-")
        assert store.list_cases()[0]["title"] == sample_case()["title"]
        assert store.get_case(saved["case_ref"])["question"] == sample_case()["question"]
        assert store.get_case(saved["case_ref"])["uploaded_documents"][0]["title"] == "projet-avenant.pdf"


def test_final_decision_is_manual_versioned_and_preserved() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory() as temporary:
        store = module.LocalCaseStore(Path(temporary) / "cases")
        saved = store.save_case(sample_case())
        updated = {
            **saved,
            "status": "CLOSED",
            "final_decision": {
                "date": "2026-07-31",
                "type": "NEGOTIATED_SOLUTION",
                "author_role": "Direction et délégation syndicale",
                "summary": "Maintien en journée après négociation.",
                "supporting_document": "Courrier de confirmation",
            },
        }
        result = store.save_case(updated)

        assert result["case_ref"] == saved["case_ref"]
        assert result["created_at"] == saved["created_at"]
        assert result["status"] == "CLOSED"
        assert result["final_decision"]["summary"].startswith("Maintien")
        assert store.list_cases()[0]["decision_recorded"] is True


def test_internal_identifiers_are_never_stored_in_the_case_file() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "cases"
        store = module.LocalCaseStore(root)
        saved = store.save_case(sample_case())
        raw = (root / f"{saved['case_ref']}.json").read_text(encoding="utf-8")

        assert "query_id" not in raw
        assert "fact_id" not in raw
        assert "query-private" not in raw
        assert "fact-private" not in raw


def test_local_paths_are_rejected_instead_of_being_persisted() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory() as temporary:
        store = module.LocalCaseStore(Path(temporary) / "cases")
        payload = sample_case()
        payload["notes"] = "Voir C:\\Users\\personne\\document.pdf"
        try:
            store.save_case(payload)
        except ValueError as exc:
            assert "information technique" in str(exc)
        else:  # pragma: no cover - explicit safety assertion.
            raise AssertionError("Un chemin local a été accepté.")


def test_case_can_be_deleted_explicitly() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory() as temporary:
        store = module.LocalCaseStore(Path(temporary) / "cases")
        saved = store.save_case(sample_case())
        store.delete_case(saved["case_ref"])
        assert store.list_cases() == []


def test_ui_and_server_expose_local_cases_without_automatic_persistence() -> None:
    html = (ROOT / "apps" / "nexus-local-interface" / "index.html").read_text(
        encoding="utf-8"
    )
    script = (ROOT / "apps" / "nexus-local-interface" / "app.js").read_text(
        encoding="utf-8"
    )
    server = (ROOT / "apps" / "nexus-local-interface" / "server.py").read_text(
        encoding="utf-8"
    )

    assert 'id="saveCaseButton"' in html
    assert 'id="casesView"' in html
    assert 'id="caseDecisionSummary"' in html
    assert "Enregistrer comme dossier" in html
    assert "caseSaveForm.addEventListener(\"submit\", createLocalCase)" in script
    assert 'button.dataset.secondaryAction === "cases"' in script
    assert '"/api/local-cases"' in server
    assert "LOCAL_CASE_STORE.save_case(payload)" in server
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "situation_summary: shortAnswer.textContent.trim()" in script
    assert "uploaded_documents:" in script
    assert "Pièces conservées dans le dossier" in script
    assert 'caseBackToList.addEventListener("click", openLocalCases)' in script
