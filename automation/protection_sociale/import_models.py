"""Import record models for Protection sociale LOT 1A."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field

SCHEMA_VERSION="1.0"; IMPORT_VERSION="1.0"
@dataclass
class ExtractionResult:
    text_content:str=""; status:str="extracted"; extractor_name:str="none"; extractor_method:str="not_attempted"
    page_count:int|None=None; paragraph_count:int|None=None; table_count:int|None=None
    warnings:list[str]=field(default_factory=list)

@dataclass
class ImportedDocument:
    document_id:str; source_relative_path:str; source_filename:str; source_extension:str; source_size_bytes:int; source_sha256:str; source_modified_at:str
    document_domain_hint:str; document_category_hint:str; document_subcategory_hint:str|None
    extractor_name:str; extractor_method:str; extraction_status:str; extraction_error_code:str|None; extraction_error_message:str|None
    text_content:str; text_length:int; page_count:int|None; paragraph_count:int|None; table_count:int|None
    duplicate_group_id:str|None; is_exact_duplicate:bool; is_empty_source:bool; warnings:list[str]; imported_at:str
    schema_version:str=SCHEMA_VERSION
    def to_dict(self)->dict: return asdict(self)
