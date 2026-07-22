from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import NEXUS_RUNTIME_INTEGRATION.protection_sociale_search as search_module
from NEXUS_RUNTIME_INTEGRATION import RuntimeProtectionSocialeConfig
from NEXUS_RUNTIME_INTEGRATION.protection_sociale_search import RuntimeProtectionSocialeGateway
from automation.protection_sociale.chunk_models import Chunk


def chunk(document_id="synthetic-document", index=0, topic="optique"):
    return Chunk(
        chunk_id=f"synthetic-chunk-{index}", document_id=document_id,
        source_document_id=f"synthetic-source-{document_id}", metadata_record_id="synthetic-metadata",
        source_relative_path="SYNTHETIC/notice.json", source_sha256="a" * 64,
        chunk_index=index, chunk_count=1, chunk_type="paragraph",
        text="SYNTHETIC RAW CONTENT MUST NOT LEAVE THE GATEWAY",
        text_length_chars=48, estimated_token_count=12,
        metadata_snapshot={
            "domaine_principal": {"value": "mutuelle"},
            "sous_domaine": {"value": topic},
            "type_document": {"value": "notice"},
        },
        source_quality_level="good", metadata_quality_level="good",
        chunk_quality_score=80, chunk_quality_level="good",
        created_at="2026-07-22T12:00:00+00:00", unique_text_length_chars=48,
    )


def write_chunks(root: Path, values=None):
    directory = root / "chunks"
    directory.mkdir(parents=True)
    values = values or (chunk(),)
    path = directory / "synthetic.jsonl"
    path.write_text("".join(json.dumps(asdict(item), ensure_ascii=False) + "\n" for item in values), encoding="utf-8")
    return path


def digest(root: Path):
    sha = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            sha.update(path.relative_to(root).as_posix().encode())
            sha.update(path.read_bytes())
    return sha.hexdigest()


def answer(query="Que couvre la mutuelle pour l'optique ?"):
    return {"query": query, "route": {"domains": ["protection_sociale"]}}


def test_gateway_calls_existing_chunk_model_and_returns_metadata_only(tmp_path, monkeypatch):
    write_chunks(tmp_path)
    calls = {"chunk": 0}
    real_chunk = search_module.Chunk

    def tracked_chunk(**values):
        calls["chunk"] += 1
        return real_chunk(**values)

    monkeypatch.setattr(search_module, "Chunk", tracked_chunk)
    result = RuntimeProtectionSocialeGateway(
        RuntimeProtectionSocialeConfig(True, tmp_path)
    ).search(answer())
    assert calls["chunk"] == 1
    assert result.document_count == 1
    assert result.chunk_count == 1
    rendered = repr(result)
    assert "SYNTHETIC RAW CONTENT" not in rendered
    assert "SYNTHETIC/notice.json" not in rendered
    assert result.documents[0].topic == "optique"


def test_gateway_is_deterministic_bounded_and_read_only(tmp_path):
    path = write_chunks(tmp_path, (
        chunk("synthetic-b", 0), chunk("synthetic-a", 0), chunk("synthetic-c", 0),
    ))
    before = digest(tmp_path)
    config = RuntimeProtectionSocialeConfig(True, tmp_path, max_documents=2, max_chunks=2)
    first = RuntimeProtectionSocialeGateway(config).search(answer())
    second = RuntimeProtectionSocialeGateway(config).search(answer())
    assert tuple(item.document_id for item in first.documents) == ("synthetic-a", "synthetic-b")
    assert first.documents == second.documents
    assert digest(tmp_path) == before
    assert path.exists()


def test_gateway_rejects_missing_corpus_and_metadata_miss(tmp_path):
    unavailable = RuntimeProtectionSocialeGateway(
        RuntimeProtectionSocialeConfig(True, tmp_path / "missing")
    ).search(answer())
    assert unavailable.fallback_code == "PROTECTION_SOCIALE_UNAVAILABLE"
    write_chunks(tmp_path, (chunk(topic="dentaire"),))
    missing = RuntimeProtectionSocialeGateway(
        RuntimeProtectionSocialeConfig(True, tmp_path)
    ).search(answer("Question sur un sujet sans correspondance"))
    assert missing.fallback_code == "PROTECTION_SOCIALE_NO_RESULT"
