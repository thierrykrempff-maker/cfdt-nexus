"""Traceable metadata models for Protection sociale LOT 1C."""
from __future__ import annotations
from dataclasses import asdict,dataclass,field
from typing import Any
SCHEMA_VERSION="1.0"; EXTRACTION_VERSION="1.0"
@dataclass
class MetadataValue:
    value:Any=None; source:str|None=None; confidence_level:str="very_low"; confidence_score:float=0.0; warnings:list[str]=field(default_factory=list)
@dataclass
class MetadataRecord:
    metadata_record_id:str; document_id:str; source_document_id:str; source_relative_path:str; source_sha256:str
    extraction_status:str; metadata:dict[str,MetadataValue]; conflicts:list[dict]; warnings:list[str]; extracted_at:str
    metadata_quality_score:int; metadata_quality_level:str; extraction_version:str=EXTRACTION_VERSION; schema_version:str=SCHEMA_VERSION
    def to_dict(self)->dict:return asdict(self)
