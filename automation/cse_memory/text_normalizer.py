"""Normalize LOT 1A extracted text locally without OCR, AI, or network."""

from __future__ import annotations

import argparse
import json
import math
import re
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation.cse_memory.document_importer import redact_absolute_paths
from automation.cse_memory.normalized_models import NORMALIZATION_VERSION, NormalizedDocument, TextBlock
from automation.cse_memory.text_quality import assess_quality


SEPARATOR_PATTERN = re.compile(r"^---\s+(PAGE|SLIDE|SHEET)\s+(.+?)\s+---$", re.IGNORECASE)
CONTROL_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
HYPHENATION_PATTERN = re.compile(r"([A-Za-zÀ-ÖØ-öø-ÿ]{3,})-\n([a-zà-öø-ÿ]{3,})")
QUOTE_TRANSLATION = str.maketrans({
    "’": "'", "‘": "'", "‛": "'", "“": '"', "”": '"', "„": '"',
    "«": '"', "»": '"', "–": "-", "—": "-", "‐": "-", "‑": "-",
})


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalized_document_id(source_document_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"cfdt-nexus:cse:normalized:{source_document_id}:{NORMALIZATION_VERSION}"))


def normalize_text(text: str) -> tuple[str, list[str]]:
    transformations: list[str] = []
    value = text
    updated = value.replace("\r\n", "\n").replace("\r", "\n")
    if updated != value:
        transformations.append("line_endings_normalized")
    value = updated
    updated = CONTROL_PATTERN.sub("", value)
    if updated != value:
        transformations.append("control_characters_removed")
    value = updated
    updated = value.translate(QUOTE_TRANSLATION)
    if updated != value:
        transformations.append("typographic_quotes_and_dashes_normalized")
    value = updated
    updated = HYPHENATION_PATTERN.sub(r"\1\2", value)
    if updated != value:
        transformations.append("probable_line_hyphenation_joined")
    value = updated
    lines = []
    spaces_changed = False
    punctuation_changed = False
    for line in value.split("\n"):
        if SEPARATOR_PATTERN.match(line.strip()):
            lines.append(line.strip())
            continue
        cleaned = re.sub(r"[ \t]+", " ", line).strip()
        spaces_changed = spaces_changed or cleaned != line
        punctuated = re.sub(r"\s+([,.%])", r"\1", cleaned)
        punctuated = re.sub(r"([,.!?;:])(?=[A-Za-zÀ-ÖØ-öø-ÿ])", r"\1 ", punctuated)
        punctuated = re.sub(r"\s*'\s*", "'", punctuated)
        punctuation_changed = punctuation_changed or punctuated != cleaned
        lines.append(punctuated)
    if spaces_changed:
        transformations.append("horizontal_spaces_normalized")
    if punctuation_changed:
        transformations.append("unambiguous_punctuation_spacing_normalized")
    updated = "\n".join(lines)
    compact = re.sub(r"\n{3,}", "\n\n", updated).strip()
    if compact != updated.strip():
        transformations.append("excessive_blank_lines_reduced")
    return compact, transformations


def split_sections(text: str) -> list[tuple[str | None, str, str]]:
    sections: list[tuple[str | None, str, str]] = []
    locator: str | None = None
    separator = ""
    content: list[str] = []
    for line in text.splitlines():
        match = SEPARATOR_PATTERN.match(line.strip())
        if match:
            if content or separator:
                sections.append((locator, separator, "\n".join(content).strip()))
            locator = f"{match.group(1).casefold()} {match.group(2).strip()}"
            separator = line.strip()
            content = []
        else:
            content.append(line)
    if content or separator or not sections:
        sections.append((locator, separator, "\n".join(content).strip()))
    return sections


def repeated_header_footer_candidates(
    text: str, *, min_sections: int = 3, repetition_ratio: float = 0.70,
    max_line_length: int = 80,
) -> set[str]:
    sections = [section for section in split_sections(text) if section[0] and section[2]]
    if len(sections) < min_sections:
        return set()
    candidates: list[str] = []
    for _, _, content in sections:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if lines:
            for line in {lines[0], lines[-1]}:
                if 2 <= len(line) <= max_line_length and len(line.split()) <= 12:
                    candidates.append(line)
    threshold = max(min_sections, math.ceil(len(sections) * repetition_ratio))
    return {line for line, count in Counter(candidates).items() if count >= threshold}


def remove_repeated_lines(text: str, candidates: set[str]) -> tuple[str, list[str]]:
    if not candidates:
        return text, []
    removed: list[str] = []
    output: list[str] = []
    for line in text.splitlines():
        if line.strip() in candidates and not SEPARATOR_PATTERN.match(line.strip()):
            removed.append(line.strip())
        else:
            output.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(output)).strip(), sorted(set(removed))


def _block_type(text: str) -> str:
    if re.match(r"^(?:[-*•]|\d+[.)])\s+", text):
        return "list_item"
    if "\t" in text:
        return "table_row"
    if len(text) <= 100 and (text.isupper() or text.endswith(":")):
        return "heading_candidate"
    return "paragraph" if "\n" not in text else "text_block"


def generate_blocks(text: str, document_id: str) -> list[TextBlock]:
    blocks: list[TextBlock] = []
    ordinal = 0
    for locator, separator, content in split_sections(text):
        if separator:
            ordinal += 1
            blocks.append(TextBlock(
                block_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document_id}:block:{ordinal}")),
                block_type="separator", ordinal=ordinal, source_locator=locator,
                text=separator, text_length=len(separator),
            ))
        for paragraph in re.split(r"\n\s*\n", content):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            ordinal += 1
            blocks.append(TextBlock(
                block_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document_id}:block:{ordinal}")),
                block_type=_block_type(paragraph), ordinal=ordinal,
                source_locator=locator, text=paragraph, text_length=len(paragraph),
            ))
    return blocks


def language_hint(text: str) -> str | None:
    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", text.casefold())
    if len(words) < 20:
        return None
    counts = Counter(words)
    french = sum(counts[word] for word in ("le", "la", "les", "des", "une", "est", "dans", "pour", "avec"))
    english = sum(counts[word] for word in ("the", "and", "of", "to", "is", "in", "for", "with"))
    if french >= 3 and french > english * 1.5:
        return "fr"
    if english >= 3 and english > french * 1.5:
        return "en"
    return "undetermined"


def normalize_document(source: dict[str, Any], *, remove_headers_footers: bool = False) -> NormalizedDocument:
    source_id = str(source["document_id"])
    document_id = normalized_document_id(source_id)
    original_text = str(source.get("text_content") or "")
    normalized, transformations = normalize_text(original_text)
    candidates = repeated_header_footer_candidates(normalized)
    removed: list[str] = []
    if remove_headers_footers and candidates:
        normalized, removed = remove_repeated_lines(normalized, candidates)
        if removed:
            transformations.append("high_confidence_repeated_headers_footers_removed")
    safe_text, redacted = redact_absolute_paths(normalized)
    if redacted:
        transformations.append("absolute_paths_redacted")
    blocks = generate_blocks(safe_text, document_id)
    quality = assess_quality(safe_text, source, len(blocks))
    status = "empty" if not safe_text else "normalized_with_warnings" if quality["flags"] else "normalized"
    warnings = list(quality["warnings"])
    if candidates and not remove_headers_footers:
        warnings.append(f"repeated_header_footer_candidates:{len(candidates)}")
    safe_removed, _ = redact_absolute_paths(removed)
    return NormalizedDocument(
        document_id=document_id, source_document_id=source_id,
        source_relative_path=str(source["source_relative_path"]),
        source_sha256=str(source["source_sha256"]),
        source_extraction_status=str(source.get("extraction_status", "unknown")),
        normalization_status=status, normalization_version=NORMALIZATION_VERSION,
        original_text_length=len(original_text), normalized_text_length=len(safe_text),
        normalized_text=safe_text, blocks=blocks, block_count=len(blocks),
        page_count=source.get("page_count"), slide_count=source.get("slide_count"),
        sheet_count=source.get("sheet_count"), detected_language_hint=language_hint(safe_text),
        quality_score=quality["score"], quality_level=quality["level"],
        quality_flags=quality["flags"], transformations_applied=transformations,
        removed_repeated_lines=safe_removed, warnings=warnings, normalized_at=utc_now(),
        technical_metadata={"repeated_header_footer_candidate_count": len(candidates)},
    )


def validate_paths(source: Path, output: Path) -> tuple[Path, Path]:
    source = source.resolve()
    output = output.resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"LOT 1A source does not exist: {source}")
    lower_source_parts = {part.casefold() for part in source.parts}
    if "raw_documents" in lower_source_parts:
        raise ValueError("LOT 1B source must not be RAW_DOCUMENTS")
    lower_output_parts = {part.casefold() for part in output.parts}
    if "raw_documents" in lower_output_parts or "lot_1a" in lower_output_parts:
        raise ValueError("LOT 1B output must not be RAW_DOCUMENTS or LOT_1A")
    if output == source or source in output.parents:
        raise ValueError("LOT 1B output must not be inside its source")
    return source, output


def discover_records(
    source: Path, *, statuses: set[str] | None = None, extensions: set[str] | None = None,
    subfolder: str | None = None,
) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(source.glob("*.json"), key=lambda item: item.name.casefold()):
        if path.is_symlink():
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            paths.append(path)
            continue
        relative = str(record.get("source_relative_path", ""))
        if subfolder and not relative.casefold().startswith(subfolder.replace("\\", "/").strip("/").casefold() + "/"):
            continue
        if statuses and str(record.get("extraction_status", "")).casefold() not in statuses:
            continue
        if extensions and str(record.get("source_extension", "")).casefold() not in extensions:
            continue
        paths.append(path)
    return paths


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _summary(manifest: dict[str, Any]) -> str:
    statuses = "\n".join(f"- {key}: {value}" for key, value in manifest["status_counts"].items())
    levels = "\n".join(f"- {key}: {value}" for key, value in manifest["quality_levels"].items())
    return f"""# Normalisation locale — LOT 1B

- Mode : {manifest['mode']}
- Documents examinés : {manifest['examined_count']}
- Documents normalisés : {manifest['normalized_count']}
- Documents repris : {manifest['resumed_count']}
- Longueur avant : {manifest['original_text_length_total']}
- Longueur après : {manifest['normalized_text_length_total']}
- Blocs : {manifest['block_count_total']}
- Candidats en-tête/pied : {manifest['header_footer_candidate_count']}
- Durée : {manifest['duration_seconds']:.3f} secondes

## Statuts

{statuses or '- Aucun'}

## Niveaux qualité

{levels or '- Aucun'}

Traitement local déterministe, sans OCR, réseau, IA externe, analyse métier ou indexation.
"""


def run_normalization(
    source: Path | str, output: Path | str, *, mode: str = "dry-run",
    statuses: set[str] | None = None, extensions: set[str] | None = None,
    subfolder: str | None = None, limit: int | None = None, force: bool = False,
    remove_headers_footers: bool = False,
) -> dict[str, Any]:
    source, output = validate_paths(Path(source), Path(output))
    if mode not in {"dry-run", "normalize"}:
        raise ValueError("Mode must be dry-run or normalize")
    normalized_statuses = {item.casefold() for item in statuses or set()}
    normalized_extensions = {item.casefold() if item.startswith(".") else f".{item.casefold()}" for item in extensions or set()}
    paths = discover_records(
        source, statuses=normalized_statuses or None, extensions=normalized_extensions or None,
        subfolder=subfolder,
    )
    if limit is not None:
        paths = paths[:max(0, limit)]
    started = time.monotonic()
    status_counts: Counter[str] = Counter()
    quality_levels: Counter[str] = Counter()
    quality_scores: list[int] = []
    documents: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    original_total = normalized_total = block_total = candidate_total = 0
    normalized_count = resumed_count = 0

    for path in paths:
        source_id = path.stem
        try:
            source_record = json.loads(path.read_text(encoding="utf-8"))
            source_id = str(source_record["document_id"])
            output_id = normalized_document_id(source_id)
            output_path = output / "documents" / f"{output_id}.json"
            if mode == "normalize" and output_path.is_file() and not force:
                existing = json.loads(output_path.read_text(encoding="utf-8"))
                if (
                    existing.get("source_sha256") == source_record.get("source_sha256")
                    and existing.get("normalization_version") == NORMALIZATION_VERSION
                ):
                    resumed_count += 1
                    status_counts[str(existing.get("normalization_status"))] += 1
                    quality_levels[str(existing.get("quality_level"))] += 1
                    quality_scores.append(int(existing.get("quality_score", 0)))
                    original_total += int(existing.get("original_text_length", 0))
                    normalized_total += int(existing.get("normalized_text_length", 0))
                    block_total += int(existing.get("block_count", 0))
                    candidate_total += int(existing.get("technical_metadata", {}).get("repeated_header_footer_candidate_count", 0))
                    documents.append({"document_id": output_id, "source_document_id": source_id, "status": existing.get("normalization_status"), "resumed": True})
                    continue
            if mode == "dry-run":
                documents.append({"source_document_id": source_id, "planned_status": "normalizable"})
                status_counts["normalizable"] += 1
                continue
            record = normalize_document(source_record, remove_headers_footers=remove_headers_footers)
            payload = record.to_dict()
            _write_json(output_path, payload)
            normalized_count += 1
            status_counts[record.normalization_status] += 1
            quality_levels[record.quality_level] += 1
            quality_scores.append(record.quality_score)
            original_total += record.original_text_length
            normalized_total += record.normalized_text_length
            block_total += record.block_count
            candidate_total += int(record.technical_metadata["repeated_header_footer_candidate_count"])
            documents.append({
                "document_id": record.document_id, "source_document_id": source_id,
                "status": record.normalization_status, "quality_score": record.quality_score,
                "quality_level": record.quality_level, "block_count": record.block_count,
                "resumed": False,
            })
        except Exception as error:
            status_counts["failed"] += 1
            safe_error, _ = redact_absolute_paths(str(error)[:500])
            errors.append({
                "source_document_id": source_id, "error_code": type(error).__name__,
                "error_message": safe_error,
            })

    manifest = {
        "schema_version": "1.0", "normalization_version": NORMALIZATION_VERSION,
        "mode": mode, "generated_at": utc_now(), "examined_count": len(paths),
        "normalized_count": normalized_count, "resumed_count": resumed_count,
        "status_counts": dict(sorted(status_counts.items())),
        "quality_levels": dict(sorted(quality_levels.items())),
        "quality_score_min": min(quality_scores) if quality_scores else None,
        "quality_score_max": max(quality_scores) if quality_scores else None,
        "quality_score_average": round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else None,
        "original_text_length_total": original_total,
        "normalized_text_length_total": normalized_total,
        "block_count_total": block_total,
        "header_footer_candidate_count": candidate_total,
        "error_count": len(errors), "duration_seconds": round(time.monotonic() - started, 3),
        "documents": documents,
    }
    if mode == "normalize":
        _write_json(output / "manifests" / "normalization_manifest.json", manifest)
        (output / "manifests").mkdir(parents=True, exist_ok=True)
        (output / "manifests" / "normalization_summary.md").write_text(_summary(manifest), encoding="utf-8")
        _write_json(output / "logs" / "normalization_errors.json", {"errors": errors})
        _write_json(output / "manifests" / "quality_report.json", {
            "quality_levels": manifest["quality_levels"],
            "quality_score_min": manifest["quality_score_min"],
            "quality_score_max": manifest["quality_score_max"],
            "quality_score_average": manifest["quality_score_average"],
            "document_count": len(quality_scores),
        })
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("dry-run", "normalize"), default="dry-run")
    parser.add_argument("--status", action="append", dest="statuses")
    parser.add_argument("--extension", action="append", dest="extensions")
    parser.add_argument("--subfolder")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--remove-repeated-headers-footers", action="store_true")
    args = parser.parse_args()
    manifest = run_normalization(
        args.source, args.output, mode=args.mode, statuses=set(args.statuses or []),
        extensions=set(args.extensions or []), subfolder=args.subfolder, limit=args.limit,
        force=args.force, remove_headers_footers=args.remove_repeated_headers_footers,
    )
    print(json.dumps({key: manifest[key] for key in (
        "mode", "examined_count", "normalized_count", "resumed_count", "status_counts",
        "quality_levels", "quality_score_min", "quality_score_max", "quality_score_average",
        "original_text_length_total", "normalized_text_length_total", "block_count_total",
        "header_footer_candidate_count", "error_count", "duration_seconds",
    )}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
