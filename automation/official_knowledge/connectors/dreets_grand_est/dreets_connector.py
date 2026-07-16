"""Future connector contract. Every operation is unavailable in LOT 2A."""
from __future__ import annotations
from typing import Protocol
from . import DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED
from .dreets_models import DreetsResourceCandidate

class DreetsGrandEstConnectorContract(Protocol):
 def discover_resources(self,query_or_scope:str)->list[DreetsResourceCandidate]:...
 def fetch_resource(self,candidate:DreetsResourceCandidate)->bytes:...
 def classify_resource(self,candidate:DreetsResourceCandidate):...

class DreetsGrandEstConnector:
 enabled=False
 connector_status="architecture_only"
 def discover_resources(self,_query_or_scope:str):raise RuntimeError(DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED)
 def fetch_resource(self,_candidate:DreetsResourceCandidate):raise RuntimeError(DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED)
 def classify_resource(self,_candidate:DreetsResourceCandidate):raise RuntimeError(DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED)
