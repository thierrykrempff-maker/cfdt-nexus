"""Deterministic quality and coverage checks for LOT 1D."""
from __future__ import annotations
import re

def quality_level(score: int) -> str:
    if score >= 90: return "excellent"
    if score >= 75: return "good"
    if score >= 55: return "acceptable"
    if score >= 30: return "poor"
    return "unusable"

def assess_chunk(text: str, unique_length: int, min_chars: int, max_chars: int,
                 overlap: int, source_quality: str, locators: list[str],
                 metadata: dict, strict_cut: bool=False, duplicate: bool=False) -> tuple[int,str,list[str]]:
    flags=[]; score=100
    if not text: flags.append("empty_chunk"); score=0
    if unique_length and unique_length < min_chars: flags.append("chunk_too_short"); score-=15
    if len(text) > max_chars: flags.append("chunk_too_long"); score-=35
    if strict_cut: flags.append("strict_cut"); score-=12
    if text and overlap > len(text)*0.45: flags.append("excessive_overlap"); score-=18
    if duplicate: flags.append("abnormal_duplication"); score-=20
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text): flags.append("suspicious_characters"); score-=20
    if source_quality in {"poor","unusable"}: flags.append("low_quality_source"); score-=20
    if not locators: flags.append("missing_locator"); score-=5
    if not any((metadata.get(k) or {}).get("value") for k in ("meeting_date","year","instance","document_kind","title")):
        flags.append("minimal_metadata_absent"); score-=5
    score=max(0,min(100,score)); return score,quality_level(score),flags

def validate_coverage(source_text: str, unique_parts: list[str]) -> dict:
    rebuilt="".join(unique_parts)
    lost=max(0,len(source_text)-len(rebuilt))
    return {"source_characters":len(source_text),"unique_characters_covered":len(rebuilt),
            "lost_characters":lost,"coverage_rate":100.0 if source_text==rebuilt else (100*len(rebuilt)/len(source_text) if source_text else 100.0),
            "reconstruction_ok":source_text==rebuilt,"warnings":[] if source_text==rebuilt else ["reconstruction_mismatch"]}
