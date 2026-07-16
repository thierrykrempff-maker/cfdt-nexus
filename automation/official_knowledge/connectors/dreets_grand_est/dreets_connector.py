"""Future connector contract. Every operation is unavailable in LOT 2A."""
from __future__ import annotations
from typing import Protocol
from .dreets_models import DreetsResourceCandidate
from .dreets_platform import DREETS_CAPABILITIES,DREETS_HEALTH,DREETS_METRICS,DREETS_PLATFORM_CONTRACT,DREETS_REGISTRY,DREETS_STATISTICS,DREETS_VALIDATION,network_not_implemented

class DreetsGrandEstConnectorContract(Protocol):
 def discover_resources(self,query_or_scope:str)->list[DreetsResourceCandidate]:...
 def fetch_resource(self,candidate:DreetsResourceCandidate)->bytes:...
 def classify_resource(self,candidate:DreetsResourceCandidate):...

class DreetsGrandEstConnector:
 platform_contract=DREETS_PLATFORM_CONTRACT
 platform_registry=DREETS_REGISTRY
 platform_validation=DREETS_VALIDATION
 capabilities=DREETS_CAPABILITIES
 health=DREETS_HEALTH
 statistics=DREETS_STATISTICS
 metrics=DREETS_METRICS
 enabled=platform_contract.enabled
 connector_status=platform_contract.state.value
 def discover_resources(self,_query_or_scope:str):raise network_not_implemented()
 def fetch_resource(self,_candidate:DreetsResourceCandidate):raise network_not_implemented()
 def classify_resource(self,_candidate:DreetsResourceCandidate):raise network_not_implemented()
