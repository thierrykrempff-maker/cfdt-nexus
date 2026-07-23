from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import sys

from NEXUS_RUNTIME_INTEGRATION import sanitize_public_payload


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"
APP_PATH = ROOT / "apps" / "nexus-local-interface" / "app.js"
FORBIDDEN = (
    re.compile(r"(?i)(?<![a-z0-9])[a-z]:[\\/]"),
    re.compile(r"(?i)/(?:tmp|home|users)/"),
    re.compile(r"(?i)chunk(?:_id|[-_:])"),
    re.compile(r"(?i)\bstorage_id\b"),
    re.compile(r"(?i)\buuid\b"),
    re.compile(r"(?i)\b(?:CCSEMEMORYENGINE|PROTECTION_SOCIALE_ENGINE|LOT_1D)\b"),
    re.compile(r"(?:apps|automation|NEXUS_CORE|NEXUS_RUNTIME_INTEGRATION)/"),
    re.compile(r"(?i)\b(?:bible_accords|nexus_bible_bridge|judilibre_jurisprudence|legifrance_code_travail)\b"),
    re.compile(r"(?i)\b[0-9a-f]{32,128}\b"),
    re.compile(r"(?i)\bruntime-[a-z0-9_-]{8,}\b"),
)


def load_server():
    sys.path.insert(0, str(SERVER_PATH.parent))
    spec = importlib.util.spec_from_file_location("nexus_public_confidentiality_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def private_payload() -> dict[str, object]:
    digest = "a1" * 32
    return {
        "ok": True,
        "answer": {
            "short_answer": "Réponse métier conservée.",
            "route": {"domains": ["temps_travail"], "engines": ["internal-engine"]},
            "sources": [
                {
                    "document": "Accord INEOS Temps de travail",
                    "origin": "bible_accords",
                    "chunk_id": "chunk_private_001",
                    "storage_id": "storage-private",
                    "source_sha256": digest,
                    "url": "C:\\internal\\corpus\\agreement.txt",
                    "excerpt": "Information métier utile.",
                },
                {
                    "document": "Code du travail",
                    "origin": "legifrance_code_travail",
                    "official_id": "LEGIARTI-SYNTHETIC",
                    "url": "https://www.legifrance.gouv.fr/",
                },
            ],
        },
        "orchestration": {
            "reponse_synthetique_nexus": "Réponse métier conservée.",
            "diagnostics": {"storage_id": "private"},
        },
        "runtime_integration": {"diagnostics": {"request_id": "runtime-private"}},
        "analysis_report": {
            "generated_from": [
                "automation/scripts/assistant_ds_router.py: ask --format json",
                "automation/scripts/cdtn_connector.py: search_sources",
                "NEXUS_CORE/orchestration: PipelineExecutor",
            ],
            "sections": [
                {
                    "id": "core_v3_runtime",
                    "title": "Analyse",
                    "items": [
                        "Source | chunk chunk_private_001 | url/id D:\\private\\document.txt",
                        "Référence /tmp/private/document.txt",
                        "Identifiant 123e4567-e89b-12d3-a456-426614174000",
                    ],
                }
            ],
            "markdown": (
                "Rapport métier\n"
                "chunk_id=chunk_private_001\n"
                "/home/private/corpus/file.txt\n"
                f"hash {digest}\n"
                "CCSEMEMORYENGINE/PROCESSED/LOT_1D"
            ),
        },
    }


def assert_no_private_reference(payload: dict[str, object]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False)
    for pattern in FORBIDDEN:
        assert not pattern.search(serialized), pattern.pattern
    for key in (
        "chunk_id",
        "source_sha256",
        "storage_id",
        "runtime_integration",
        "diagnostics",
    ):
        assert f'"{key}"' not in serialized


def test_public_payload_removes_paths_identifiers_and_internal_diagnostics() -> None:
    public = sanitize_public_payload(private_payload())
    assert_no_private_reference(public)
    assert public["answer"]["short_answer"] == "Réponse métier conservée."
    assert public["answer"]["sources"][0]["document"] == "Accord INEOS Temps de travail"
    assert public["answer"]["sources"][0]["origin"] == "Accords INEOS"
    assert public["answer"]["sources"][1]["official_id"] == "LEGIARTI-SYNTHETIC"
    assert public["answer"]["sources"][1]["url"] == "https://www.legifrance.gouv.fr/"
    assert public["analysis_report"]["generated_from"] == [
        "Routeur Nexus",
        "Code du travail numérique",
        "Nexus Core",
    ]


def test_public_payload_does_not_mutate_internal_runtime_payload() -> None:
    internal = private_payload()
    public = sanitize_public_payload(internal)
    assert internal["answer"]["sources"][0]["chunk_id"] == "chunk_private_001"
    assert "runtime_integration" in internal
    assert "runtime_integration" not in public


def test_server_public_entrypoint_applies_boundary(monkeypatch) -> None:
    server = load_server()
    internal = private_payload()
    monkeypatch.setattr(server, "analyze_question", lambda *_args, **_kwargs: internal)
    public = server.analyze_public_question("Question synthétique")
    assert_no_private_reference(public)
    assert internal["answer"]["sources"][0]["chunk_id"] == "chunk_private_001"


def test_frontend_has_no_chunk_identifier_rendering() -> None:
    source = APP_PATH.read_text(encoding="utf-8")
    assert "source.chunk_id" not in source
