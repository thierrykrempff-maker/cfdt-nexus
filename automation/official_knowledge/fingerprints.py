"""Deterministic fingerprints for synthetic/local values."""
import hashlib
from urllib.parse import urlsplit,urlunsplit

def content_sha256(content:bytes|str)->str:
    return hashlib.sha256(content.encode("utf-8") if isinstance(content,str) else content).hexdigest()
def canonicalize_uri(uri:str)->str:
    p=urlsplit(uri); return urlunsplit((p.scheme.casefold(),(p.hostname or "").casefold(),p.path or "/",p.query,""))
def uri_fingerprint(uri:str)->str:return content_sha256(canonicalize_uri(uri))
def version_id(source_id:str,uri:str,content_hash:str)->str:return content_sha256(f"{source_id}\0{canonicalize_uri(uri)}\0{content_hash}")
def content_unchanged(previous_hash:str,current:bytes|str)->bool:return previous_hash==content_sha256(current)
def is_new_version(previous_hash:str,current:bytes|str)->bool:return not content_unchanged(previous_hash,current)
