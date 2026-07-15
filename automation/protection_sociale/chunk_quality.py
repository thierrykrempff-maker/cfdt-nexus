"""Deterministic quality and coverage controls for LOT 1D chunks."""
from __future__ import annotations

import re
from typing import Any


def quality_level(score: int) -> str:
    if score >= 90: return "excellent"
    if score >= 75: return "good"
    if score >= 55: return "acceptable"
    if score >= 30: return "poor"
    return "unusable"


def assess_chunk(text: str, unique_length: int, min_chars: int, max_chars: int,
                 overlap: int, source_quality: str, metadata: dict[str, Any],
                 has_locator: bool, strict_cut: bool, flattened_table: bool = False,
                 duplicate: bool = False) -> tuple[int, str, list[str]]:
    score = 100
    flags: list[str] = []
    penalties = {
        "chunk_too_short": 15, "chunk_too_long": 40, "strict_cut": 12,
        "excessive_overlap": 20, "suspicious_characters": 20,
        "low_quality_source": 20, "missing_locator": 5,
        "essential_metadata_absent": 8, "flattened_table": 5,
        "abnormal_duplication": 20,
    }
    if not text:
        return 0, "unusable", ["empty_chunk"]
    if unique_length < min_chars: flags.append("chunk_too_short")
    if len(text) > max_chars: flags.append("chunk_too_long")
    if strict_cut: flags.append("strict_cut")
    if overlap > len(text) * .45: flags.append("excessive_overlap")
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text): flags.append("suspicious_characters")
    if source_quality in {"poor", "unusable"}: flags.append("low_quality_source")
    if not has_locator: flags.append("missing_locator")
    if not any((metadata.get(k) or {}).get("value") for k in ("domaine_principal", "type_document", "assureur", "contrat", "référence")):
        flags.append("essential_metadata_absent")
    if flattened_table: flags.append("flattened_table")
    if duplicate: flags.append("abnormal_duplication")
    score = max(0, score - sum(penalties[f] for f in flags))
    return score, quality_level(score), flags


def validate_coverage(source_text: str, ranges: list[tuple[int, int]]) -> dict[str, Any]:
    ordered = sorted(ranges)
    cursor = 0
    losses: list[tuple[int, int]] = []
    for start, end in ordered:
        if start > cursor: losses.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < len(source_text): losses.append((cursor, len(source_text)))
    covered = len(source_text) - sum(end - start for start, end in losses)
    rebuilt = "".join(source_text[start:end] for start, end in ordered)
    return {
        "source_characters": len(source_text),
        "unique_characters_covered": covered,
        "duplicated_characters": 0,
        "coverage_rate": round(100 * covered / len(source_text), 6) if source_text else 100.0,
        "losses_detected": [{"start": a, "end": b} for a, b in losses],
        "reconstruction_ok": not losses and rebuilt == source_text,
        "reconstruction_warnings": [] if not losses and rebuilt == source_text else ["reconstruction_mismatch"],
    }
