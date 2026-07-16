"""Public-official provenance, distinct from internal corpora."""
from dataclasses import asdict,dataclass,field
from datetime import datetime

@dataclass(frozen=True)
class ProvenanceRecord:
    provenance_id:str; source_id:str; source_type:str; source_uri:str; canonical_uri:str; publisher:str
    retrieved_at:datetime|None=None; published_at:datetime|None=None; modified_at:datetime|None=None
    content_sha256:str|None=None; http_etag:str|None=None; http_last_modified:str|None=None; license_id:str|None=None
    authority_level:str="unknown"; domain_tags:tuple[str,...]=(); language:str="fr"; confidentiality_level:str="public_official"
    retrieval_method:str="planned"; connector_version:str="architecture-only"; schema_version:str="1.0"; warnings:tuple[str,...]=()
    def __post_init__(self):
        for uri in (self.source_uri,self.canonical_uri):
            if len(uri)>1 and uri[1]==":" or uri.startswith(("/home/","/Users/")): raise ValueError("absolute local path refused")
    def to_dict(self): return asdict(self)
