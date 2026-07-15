"""Deterministic, explainable quality scoring for extracted CSE text."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any


def quality_level(score: int) -> str:
    if score >= 90:
        return "excellent"
    if score >= 75:
        return "good"
    if score >= 55:
        return "acceptable"
    if score >= 25:
        return "poor"
    return "unusable"


def assess_quality(text: str, source: dict[str, Any], block_count: int) -> dict[str, Any]:
    score = 100
    flags: list[str] = []
    warnings: list[str] = []
    if not text.strip():
        return {
            "score": 0, "level": "unusable", "flags": ["empty_text"],
            "warnings": ["No usable extracted text"],
        }

    length = len(text)
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("--- ")]
    if length < 100:
        score -= 35
        flags.append("very_short_text")
    elif length < 300:
        score -= 15
        flags.append("short_text")

    non_alnum = sum(not char.isalnum() and not char.isspace() for char in text) / max(1, length)
    if non_alnum > 0.35:
        score -= 20
        flags.append("excessive_non_alphanumeric")

    normalized_lines = [re.sub(r"\s+", " ", line.casefold()) for line in lines if len(line) >= 3]
    repetitions = sum(count - 1 for count in Counter(normalized_lines).values() if count > 1)
    if normalized_lines and repetitions / len(normalized_lines) > 0.30:
        score -= 15
        flags.append("abnormal_repetition")

    if lines:
        short_ratio = sum(len(line) < 20 for line in lines) / len(lines)
        isolated_ratio = sum(len(line.split()) == 1 for line in lines) / len(lines)
        if short_ratio > 0.65 and len(lines) >= 8:
            score -= 10
            flags.append("highly_fragmented_lines")
        if isolated_ratio > 0.35 and len(lines) >= 8:
            score -= 10
            flags.append("excessive_isolated_words")
        tabular_ratio = sum("\t" in line for line in lines) / len(lines)
        if tabular_ratio > 0.60 and block_count <= 2:
            score -= 10
            flags.append("flattened_tables")

    page_count = int(source.get("page_count") or 0)
    empty_pages = sum(str(item).startswith("page_without_text:") for item in source.get("warnings", []))
    if empty_pages:
        score -= min(25, 5 + empty_pages * 3)
        flags.append("pages_without_text")
        if page_count and empty_pages / page_count >= 0.70:
            score -= 20
            flags.append("probable_image_pdf_without_ocr")

    corruption_markers = text.count("\ufffd") + sum(text.count(value) for value in ("Ã©", "Ã¨", "â€™", "\x00"))
    if corruption_markers:
        score -= min(30, 10 + corruption_markers)
        flags.extend(["potentially_corrupted_text", "suspect_encoding"])

    if length > 5_000_000:
        score -= 10
        flags.append("abnormally_large_text")
    if source.get("extraction_status") in {"extracted_with_warnings", "failed", "unreadable"}:
        score -= 8
        flags.append("partial_or_warned_extraction")

    source_size = int(source.get("source_size_bytes") or 0)
    if source_size > 100_000 and source_size / max(1, length) > 500:
        score -= 15
        flags.append("low_text_to_source_size_ratio")

    score = max(0, min(100, score))
    warnings.extend(flag.replace("_", " ") for flag in flags)
    return {"score": score, "level": quality_level(score), "flags": flags, "warnings": warnings}
