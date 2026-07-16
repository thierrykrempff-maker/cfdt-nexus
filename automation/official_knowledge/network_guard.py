"""Non-operational request interface: LOT 0 always blocks transport."""
from __future__ import annotations
from dataclasses import dataclass, field
from . import NETWORK_DISABLED
from .kill_switch import source_enabled
from .source_policy import AccessPolicy, validate_url

@dataclass(frozen=True)
class RequestSpec: source_id:str; url:str; method:str="GET"; headers:dict[str,str]=field(default_factory=dict); max_bytes:int=10_000_000
@dataclass(frozen=True)
class ResponseSpec: status_code:int; mime_type:str; body_sha256:str; size_bytes:int

class NetworkGuard:
    def authorize(self,request:RequestSpec,policy:AccessPolicy,environ=None)->None:
        validate_url(request.url,policy)
        if not source_enabled(request.source_id,environ): raise RuntimeError(NETWORK_DISABLED)
        raise RuntimeError(NETWORK_DISABLED)  # No transport can be authorized in LOT 0.
    def execute(self,*_args,**_kwargs): raise RuntimeError(NETWORK_DISABLED)
