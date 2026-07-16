"""Metadata-only model for a future local cache."""
from dataclasses import asdict,dataclass
from datetime import datetime
from pathlib import Path

@dataclass(frozen=True)
class CacheEntry:
    source_id:str; canonical_uri:str; fingerprint:str; retrieved_at:datetime; connector_version:str
    etag:str|None=None; last_modified:str|None=None; expires_at:datetime|None=None; http_status:int|None=None
    mime_type:str|None=None; size_bytes:int=0; relative_local_path:str|None=None; validation_state:str="pending"
    def __post_init__(self):
        if self.relative_local_path and (Path(self.relative_local_path).is_absolute() or len(self.relative_local_path)>1 and self.relative_local_path[1]==":"): raise ValueError("absolute cache path refused")
    def to_dict(self):return asdict(self)
