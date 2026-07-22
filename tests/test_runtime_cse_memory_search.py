from __future__ import annotations

import json

from NEXUS_RUNTIME_INTEGRATION.config import RuntimeCSEMemoryConfig
from NEXUS_RUNTIME_INTEGRATION.cse_memory_search import RuntimeCSEMemoryGateway, needs_cse_memory


def answer(query="Que disait l'ancien PV CSE sur la réorganisation ?"):
    return {
        "query": query,
        "route": {"domains": ["cse"], "intents": ["rechercher_droit_local"]},
    }


def write_chunks(root):
    chunks = root / "chunks"
    chunks.mkdir(parents=True)
    records = [
        {
            "chunk_id": "INTERNAL-CHUNK-ONE",
            "document_id": "INTERNAL-DOCUMENT-ONE",
            "chunk_index": 0,
            "indexable": True,
            "text": "Le CSE examine la réorganisation et rend un avis.",
            "unique_text_length_chars": 52,
            "source_relative_path": "confidential/internal-name.pdf",
            "source_sha256": "a" * 64,
            "created_at": "2026-01-01T00:00:00+00:00",
            "metadata_snapshot": {
                "year": {"value": 2025},
                "document_kind": {"value": "pv"},
                "instance": {"value": "CSE"},
            },
        },
        {
            "chunk_id": "INTERNAL-CHUNK-TWO",
            "document_id": "INTERNAL-DOCUMENT-TWO",
            "chunk_index": 0,
            "indexable": True,
            "text": "Sujet sans rapport avec la question posée.",
            "unique_text_length_chars": 43,
            "source_relative_path": "confidential/other.pdf",
            "source_sha256": "b" * 64,
            "created_at": "2026-01-01T00:00:00+00:00",
            "metadata_snapshot": {"document_kind": {"value": "pv"}},
        },
    ]
    (chunks / "synthetic.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records),
        encoding="utf-8",
    )


def test_detection_reuses_router_domain_and_closed_documentary_markers():
    assert needs_cse_memory(answer()) is True
    assert needs_cse_memory(answer("Quel est votre avis ?")) is True  # explicit CSE route
    assert needs_cse_memory({"query": "Quel est votre avis ?", "route": {"domains": ["paie"]}}) is False
    assert needs_cse_memory({"query": "Retrouve le PV CSE", "route": {"domains": []}}) is True


def test_read_only_gateway_finds_prepared_chunks_without_returning_text(tmp_path):
    write_chunks(tmp_path)
    result = RuntimeCSEMemoryGateway(RuntimeCSEMemoryConfig(True, tmp_path)).search(answer())
    assert result.document_count == 1
    assert result.chunk_count == 1
    assert result.fallback_code is None
    assert result.documents[0].text_content == ""


def test_no_match_and_unavailable_corpus_fail_closed(tmp_path):
    write_chunks(tmp_path)
    gateway = RuntimeCSEMemoryGateway(RuntimeCSEMemoryConfig(True, tmp_path))
    assert gateway.search(answer("Référence totalement absente xyzabc" )).fallback_code == "CSE_MEMORY_NO_MATCH"
    unavailable = RuntimeCSEMemoryGateway(RuntimeCSEMemoryConfig(True, tmp_path / "missing"))
    assert unavailable.search(answer()).fallback_code == "CSE_MEMORY_UNAVAILABLE"
