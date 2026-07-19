"""Future connector contract. Every operation is unavailable in LOT 2A."""
from __future__ import annotations
from typing import Protocol
from automation.official_knowledge.document_registry import (
 DocumentChange,DocumentRecord,DocumentRegistry,DocumentStatus,DocumentStorage,DocumentValidator,stable_document_id,
)
from .dreets_discovery import DreetsDiscoveryItem,DreetsMetadataDiscovery
from .dreets_metadata import ALLOWED_DREETS_DOMAINS,DreetsMetadata,DreetsMetadataRefusal
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
 def __init__(self,*,metadata_discovery_enabled:bool=False,discovery_quota:int=50,document_registry:DocumentRegistry|None=None):
  self._metadata_discovery=DreetsMetadataDiscovery(activated=metadata_discovery_enabled,quota=discovery_quota)
  self._document_registry=document_registry
 @property
 def metadata_discovery_enabled(self)->bool:return self._metadata_discovery.activated
 def activate_metadata_discovery(self)->"DreetsGrandEstConnector":
  return type(self)(metadata_discovery_enabled=True,discovery_quota=self._metadata_discovery.quota,document_registry=self._document_registry)
 def discover_metadata(self,items:tuple[DreetsDiscoveryItem,...],*,discovered_on:str)->tuple[DreetsMetadata,...]:
  return self._metadata_discovery.discover(items,discovered_on=discovered_on)
 def register_discovered_metadata(self,items:tuple[DreetsDiscoveryItem,...],*,discovered_on:str)->tuple[DocumentChange,...]:
  if self._document_registry is None:raise DreetsMetadataRefusal("REGISTRY_NOT_CONFIGURED","Document Registry must be explicitly configured.")
  metadata=self.discover_metadata(items,discovered_on=discovered_on);changes=[]
  for item in metadata:
   document_id=stable_document_id("dreets_grand_est",item.canonical_url)
   previous=self._document_registry.find_document(document_id)
   record=DocumentRecord(
    document_id=document_id,connector_name="dreets_grand_est",canonical_url=item.canonical_url,title=item.title,
    category=item.category,family=item.family,document_type=item.document_type,publication_date=item.date,
    first_seen=previous.first_seen if previous else item.discovered_on,last_checked=item.discovered_on,
    last_modified_metadata=previous.last_modified_metadata if previous else item.discovered_on,
    language=item.language,provenance=item.provenance,status=previous.status if previous else DocumentStatus.ACTIVE,
   )
   changes.append(self._document_registry.update_document(record) if previous else self._document_registry.register_document(record))
  return tuple(changes)
 def discover_resources(self,_query_or_scope:str):raise network_not_implemented()
 def fetch_resource(self,_candidate:DreetsResourceCandidate):raise network_not_implemented()
 def classify_resource(self,_candidate:DreetsResourceCandidate):raise network_not_implemented()

def build_dreets_document_registry(storage:DocumentStorage)->DocumentRegistry:
 return DocumentRegistry(storage,DocumentValidator({"dreets_grand_est":ALLOWED_DREETS_DOMAINS}))
