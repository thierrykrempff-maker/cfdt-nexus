"""Future transport contract. Every production operation is blocked in LOT 1A."""
from __future__ import annotations
from typing import Protocol
from . import CNIL_NETWORK_NOT_IMPLEMENTED
from .cnil_models import ParsedOfficialResource,RawOfficialResource,ResourceCandidate,ValidationResult

class CnilConnectorContract(Protocol):
 def discover_resources(self,query_or_scope:str)->list[ResourceCandidate]:...
 def fetch_resource(self,candidate:ResourceCandidate)->RawOfficialResource:...
 def validate_resource(self,raw:RawOfficialResource)->ValidationResult:...
 def parse_resource(self,raw:RawOfficialResource)->ParsedOfficialResource:...

class CnilConnector:
 def discover_resources(self,_query_or_scope:str)->list[ResourceCandidate]:raise RuntimeError(CNIL_NETWORK_NOT_IMPLEMENTED)
 def fetch_resource(self,_candidate:ResourceCandidate)->RawOfficialResource:raise RuntimeError(CNIL_NETWORK_NOT_IMPLEMENTED)
 def validate_resource(self,_raw:RawOfficialResource)->ValidationResult:raise RuntimeError(CNIL_NETWORK_NOT_IMPLEMENTED)
 def parse_resource(self,_raw:RawOfficialResource)->ParsedOfficialResource:raise RuntimeError(CNIL_NETWORK_NOT_IMPLEMENTED)
