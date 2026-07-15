"""Build local, deterministic Protection sociale LOT 1D technical chunks."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any
import uuid

from automation.protection_sociale.chunk_models import Chunk, CHUNKING_VERSION
from automation.protection_sociale.chunk_quality import assess_chunk, validate_coverage
from automation.protection_sociale.chunk_rules import ChunkConfig, estimate_tokens, locator_data, overlap_start, split_ranges

SNAPSHOT_FIELDS = (
    "domaine_principal", "sous_domaine", "type_document", "organisme_émetteur",
    "assureur", "contrat", "référence", "date_effet", "date_fin",
    "public_concerné", "thème_principal",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_chunk_id(document_id: str, index: int, start: int, end: int, source_sha256: str) -> str:
    seed = f"cfdt-nexus:protection-sociale:chunk:{document_id}:{source_sha256}:{index}:{start}:{end}:{CHUNKING_VERSION}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


def _safe_relative(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or (len(value) > 1 and value[1] == ":"):
        raise ValueError("absolute paths are refused")
    return value.replace("\\", "/")


def _guard(source: Path, metadata: Path, output: Path) -> None:
    for path in (source, metadata):
        parts = {part.casefold() for part in path.resolve().parts}
        if "raw_documents" in parts:
            raise ValueError("RAW_DOCUMENTS cannot be used as a source")
        if path.is_symlink():
            raise ValueError("symbolic links are refused")
    output_parts = {part.casefold() for part in output.resolve().parts}
    if output_parts & {"raw_documents", "lot_1a", "lot_1b", "lot_1c"}:
        raise ValueError("unsafe output location")
    if output.is_symlink():
        raise ValueError("symbolic links are refused")


def _metadata_snapshot(record: dict[str, Any] | None) -> dict[str, Any]:
    metadata = (record or {}).get("metadata", {})
    snapshot: dict[str, Any] = {}
    for key in SNAPSHOT_FIELDS:
        item = metadata.get(key, {})
        snapshot[key] = {"value": item.get("value"), "confidence_level": item.get("confidence_level", "very_low")}
    theme = snapshot["thème_principal"]
    snapshot["thèmes_principaux"] = {"value": [theme["value"]] if theme["value"] else [], "confidence_level": theme["confidence_level"]}
    # LOT 1C has no independent topic_tags field: expose only explicit theme values, never infer new tags.
    source_tags = metadata.get("topic_tags", {})
    tags = source_tags.get("value") if isinstance(source_tags, dict) else None
    snapshot["topic_tags"] = {"value": tags if isinstance(tags, list) else ([theme["value"]] if theme["value"] else []),
                              "confidence_level": source_tags.get("confidence_level", theme["confidence_level"]) if isinstance(source_tags, dict) else theme["confidence_level"]}
    return snapshot


def _metadata_quality(record: dict[str, Any] | None) -> str:
    return str((record or {}).get("metadata_quality_level") or "unusable")


def build_document(document: dict[str, Any], metadata: dict[str, Any] | None,
                   config: ChunkConfig, created_at: str | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config.validate()
    text = str(document.get("normalized_text") or "")
    document_id = str(document["document_id"])
    source_sha256 = str(document.get("source_sha256") or "")
    relative = _safe_relative(str(document.get("source_relative_path") or ""))
    snapshot = _metadata_snapshot(metadata)
    created_at = created_at or utc_now()
    source_quality = str(document.get("quality_level") or "unusable")
    metadata_quality = _metadata_quality(metadata)
    common = dict(document_id=document_id, source_document_id=str(document.get("source_document_id") or ""),
                  metadata_record_id=(metadata or {}).get("metadata_record_id"), source_relative_path=relative,
                  source_sha256=source_sha256, metadata_snapshot=snapshot, source_quality_level=source_quality,
                  metadata_quality_level=metadata_quality, created_at=created_at,
                  duplicate_group_id=document.get("duplicate_group_id"), content_id=document.get("content_id"))
    if not text:
        cid = stable_chunk_id(document_id, 0, 0, 0, source_sha256)
        chunk = Chunk(chunk_id=cid, chunk_index=0, chunk_count=1, chunk_type="empty_placeholder",
                      text="", text_length_chars=0, estimated_token_count=0, chunk_quality_score=0,
                      chunk_quality_level="unusable", quality_flags=["empty_chunk"], warnings=["no_exploitable_text"],
                      is_indexable=False, non_indexable_reason="empty_or_unusable_source", **common)
        coverage = validate_coverage("", [])
        return [chunk.to_dict()], _document_summary(document_id, [chunk.to_dict()], coverage)

    ranges = split_ranges(text, config)
    ids = [stable_chunk_id(document_id, i, start, end, source_sha256) for i, (start, end, _) in enumerate(ranges)]
    chunks: list[dict[str, Any]] = []
    for index, (start, end, strict) in enumerate(ranges):
        overlap_room = max(0, config.max_chars - (end - start))
        visible_start = start if index == 0 else overlap_start(text, start, min(config.overlap_chars, overlap_room), ranges[index - 1][0])
        chunk_text = text[visible_start:end]
        pages, paragraphs, tables, sections, chunk_type = locator_data(text, start, end)
        flattened = bool(document.get("table_count")) and not tables
        score, level, flags = assess_chunk(chunk_text, end - start, config.min_chars, config.max_chars,
                                           start - visible_start, source_quality, snapshot, bool(sections or paragraphs),
                                           strict, flattened)
        warnings = (["strict_cut_required"] if strict else []) + (["flattened_table"] if flattened else [])
        chunk = Chunk(chunk_id=ids[index], chunk_index=index, chunk_count=len(ranges), chunk_type=chunk_type,
                      text=chunk_text, text_length_chars=len(chunk_text), estimated_token_count=estimate_tokens(chunk_text),
                      source_section_ids=sections, source_block_ids=[], source_start_offset=start, source_end_offset=end,
                      page_numbers=pages, paragraph_indexes=paragraphs, table_indexes=tables,
                      previous_chunk_id=ids[index - 1] if index else None,
                      next_chunk_id=ids[index + 1] if index + 1 < len(ids) else None,
                      overlap_previous_chars=start - visible_start, overlap_next_chars=0,
                      chunk_quality_score=score, chunk_quality_level=level, quality_flags=flags, warnings=warnings,
                      is_indexable=source_quality != "unusable", non_indexable_reason="unusable_source" if source_quality == "unusable" else None,
                      unique_text_length_chars=end - start, **common)
        chunks.append(chunk.to_dict())
    for index in range(len(chunks) - 1):
        chunks[index]["overlap_next_chars"] = chunks[index + 1]["overlap_previous_chars"]
    coverage = validate_coverage(text, [(start, end) for start, end, _ in ranges])
    coverage["duplicated_characters"] = sum(c["overlap_previous_chars"] for c in chunks)
    return chunks, _document_summary(document_id, chunks, coverage)


def _document_summary(document_id: str, chunks: list[dict[str, Any]], coverage: dict[str, Any]) -> dict[str, Any]:
    return {"document_id": document_id, "chunk_count": len(chunks),
            "indexable_chunk_count": sum(bool(c["is_indexable"]) for c in chunks), "coverage": coverage}


def _matches(document: dict[str, Any], metadata: dict[str, Any] | None, filters: dict[str, str]) -> bool:
    snapshot = _metadata_snapshot(metadata)
    pairs = {"domain": "domaine_principal", "subdomain": "sous_domaine", "document_type": "type_document"}
    for option, key in pairs.items():
        if filters.get(option) and snapshot[key]["value"] != filters[option]: return False
    if filters.get("topic_tag") and filters["topic_tag"] not in snapshot["topic_tags"]["value"]: return False
    if filters.get("source_quality") and document.get("quality_level") != filters["source_quality"]: return False
    if filters.get("metadata_quality") and _metadata_quality(metadata) != filters["metadata_quality"]: return False
    if filters.get("subfolder") and filters["subfolder"].casefold() not in str(document.get("source_relative_path", "")).casefold(): return False
    return True


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(normalized_source: Path | str, metadata_source: Path | str, output: Path | str,
        config: ChunkConfig, mode: str = "dry-run", limit: int | None = None,
        force: bool = False, filters: dict[str, str] | None = None) -> dict[str, Any]:
    normalized_source, metadata_source, output = map(Path, (normalized_source, metadata_source, output))
    _guard(normalized_source, metadata_source, output)
    started = time.monotonic(); filters = filters or {}; errors: list[dict[str, str]] = []
    metadata_by_document: dict[str, dict[str, Any]] = {}
    for path in sorted(metadata_source.glob("*.json")):
        if not path.is_symlink() and path.suffix.lower() != ".lnk":
            record = json.loads(path.read_text(encoding="utf-8")); metadata_by_document[str(record.get("document_id"))] = record
    candidates = [p for p in sorted(normalized_source.glob("*.json")) if not p.is_symlink() and p.suffix.lower() != ".lnk"]
    results: list[tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]] = []; resumed = 0
    for path in candidates:
        try:
            document = json.loads(path.read_text(encoding="utf-8")); metadata = metadata_by_document.get(str(document.get("document_id")))
            if not _matches(document, metadata, filters): continue
            if limit is not None and len(results) >= limit: break
            chunks, summary = build_document(document, metadata, config)
            results.append((document, chunks, summary))
            if mode == "build":
                document_path = output / "documents" / f"{document['document_id']}.json"
                chunks_path = output / "chunks" / f"{document['document_id']}.jsonl"
                if document_path.exists() and chunks_path.exists() and not force:
                    resumed += 1; continue
                _write_json(document_path, summary)
                chunks_path.parent.mkdir(parents=True, exist_ok=True)
                chunks_path.write_text("".join(json.dumps(chunk, ensure_ascii=False) + "\n" for chunk in chunks), encoding="utf-8")
        except Exception as exc:
            errors.append({"source_file": path.name, "error_code": type(exc).__name__})
    chunks = [chunk for _, document_chunks, _ in results for chunk in document_chunks]
    coverages = [summary["coverage"] for _, _, summary in results]
    quality = Counter(chunk["chunk_quality_level"] for chunk in chunks)
    counts = [len(document_chunks) for _, document_chunks, _ in results]; sizes = [chunk["text_length_chars"] for chunk in chunks]
    stats = {
        "mode": mode, "documents_examined": len(candidates), "documents_chunked": len(results),
        "documents_resumed": resumed, "documents_non_indexable": sum(not any(c["is_indexable"] for c in cs) for _, cs, _ in results),
        "total_chunks": len(chunks), "indexable_chunks": sum(bool(c["is_indexable"]) for c in chunks),
        "chunks_per_document": _distribution(counts), "chunk_sizes": _distribution(sizes),
        "estimated_tokens": sum(c["estimated_token_count"] for c in chunks),
        "coverage_rate": round(sum(c["coverage_rate"] for c in coverages) / len(coverages), 6) if coverages else 100.0,
        "overlap_characters": sum(c["overlap_previous_chars"] for c in chunks),
        "quality_levels": dict(sorted(quality.items())), "table_chunks": sum(c["chunk_type"] == "table" for c in chunks),
        "flattened_tables": sum("flattened_table" in c["quality_flags"] for c in chunks),
        "strict_cuts": sum("strict_cut" in c["quality_flags"] for c in chunks),
        "too_short": sum("chunk_too_short" in c["quality_flags"] for c in chunks),
        "too_long": sum("chunk_too_long" in c["quality_flags"] for c in chunks),
        "errors": len(errors), "duration_seconds": round(time.monotonic() - started, 3),
    }
    if mode == "build":
        manifest = {"schema_version": "1.0", "chunking_version": CHUNKING_VERSION,
                    "configuration": config.__dict__, "statistics": stats,
                    "documents": [summary for _, _, summary in results]}
        _write_json(output / "manifests" / "chunk_manifest.json", manifest)
        _write_json(output / "manifests" / "chunk_quality_report.json", {"statistics": stats, "quality_levels": stats["quality_levels"]})
        _write_json(output / "manifests" / "chunk_coverage_report.json", {"coverage_rate": stats["coverage_rate"], "documents": [s["coverage"] | {"document_id": s["document_id"]} for _, _, s in results]})
        _write_json(output / "logs" / "chunk_errors.json", {"errors": errors})
        summary_path = output / "manifests" / "chunk_summary.md"; summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(f"# LOT 1D — synthèse technique\n\nDocuments traités : {len(results)}\n\nChunks : {len(chunks)}\n\nCouverture : {stats['coverage_rate']} %\n", encoding="utf-8")
    return stats


def _distribution(values: list[int]) -> dict[str, float | int]:
    return {"min": min(values, default=0), "average": round(sum(values) / len(values), 2) if values else 0, "max": max(values, default=0)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--normalized-source", type=Path, required=True); parser.add_argument("--metadata-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True); parser.add_argument("--mode", choices=("dry-run", "build"), default="dry-run")
    parser.add_argument("--limit", type=int); parser.add_argument("--force", action="store_true")
    parser.add_argument("--target-chars", type=int, default=1600); parser.add_argument("--max-chars", type=int, default=2500)
    parser.add_argument("--min-chars", type=int, default=300); parser.add_argument("--overlap-chars", type=int, default=200)
    for option in ("domain", "subdomain", "document-type", "topic-tag", "source-quality", "metadata-quality", "subfolder"):
        parser.add_argument("--" + option)
    parser.add_argument("--statistics-only", action="store_true")
    args = parser.parse_args(argv)
    filters = {key: getattr(args, key) for key in ("domain", "subdomain", "document_type", "topic_tag", "source_quality", "metadata_quality", "subfolder") if getattr(args, key)}
    stats = run(args.normalized_source, args.metadata_source, args.output,
                ChunkConfig(args.target_chars, args.max_chars, args.min_chars, args.overlap_chars),
                args.mode, args.limit, args.force, filters)
    print(json.dumps(stats, ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
