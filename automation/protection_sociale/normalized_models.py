"""Normalized document models for Protection sociale LOT 1B."""
from __future__ import annotations
from dataclasses import asdict,dataclass
NORMALIZATION_VERSION="1.0"; SCHEMA_VERSION="1.0"
@dataclass
class NormalizedDocument:
    document_id:str; source_document_id:str; source_relative_path:str; source_sha256:str; source_extraction_status:str
    normalization_status:str; normalization_version:str; original_text_length:int; normalized_text_length:int; normalized_text:str
    page_count:int|None; paragraph_count:int|None; table_count:int|None
    quality_score:int; quality_level:str; quality_flags:list[str]; transformations_applied:list[str]; warnings:list[str]
    normalized_at:str; schema_version:str=SCHEMA_VERSION
    def to_dict(self)->dict:return asdict(self)
