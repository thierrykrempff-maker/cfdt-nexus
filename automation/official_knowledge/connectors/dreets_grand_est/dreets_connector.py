"""Future connector contract. Every operation is unavailable in LOT 2A."""
from __future__ import annotations
from typing import Protocol
from .dreets_discovery import DreetsDiscoveryItem,DreetsMetadataDiscovery
from .dreets_metadata import DreetsMetadata
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
 metadata_discovery_activable=True
 activation_scope="METADATA_ONLY"
 def __init__(self,*,metadata_discovery_enabled:bool=False,discovery_quota:int=50):
  self._metadata_discovery=DreetsMetadataDiscovery(activated=metadata_discovery_enabled,quota=discovery_quota)
 @property
 def metadata_discovery_enabled(self)->bool:return self._metadata_discovery.activated
 def activate_metadata_discovery(self)->"DreetsGrandEstConnector":
  return type(self)(metadata_discovery_enabled=True,discovery_quota=self._metadata_discovery.quota)
 def discover_metadata(self,items:tuple[DreetsDiscoveryItem,...],*,discovered_on:str)->tuple[DreetsMetadata,...]:
  return self._metadata_discovery.discover(items,discovered_on=discovered_on)
 def discover_resources(self,_query_or_scope:str):raise network_not_implemented()
 def fetch_resource(self,_candidate:DreetsResourceCandidate):raise network_not_implemented()
 def classify_resource(self,_candidate:DreetsResourceCandidate):raise network_not_implemented()
