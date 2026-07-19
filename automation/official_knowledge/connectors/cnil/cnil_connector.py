"""Future transport contract. Every production operation is blocked in LOT 1A."""
from __future__ import annotations
from typing import Protocol
from automation.official_knowledge.document_registry import DocumentChange,DocumentRecord,DocumentRegistry,DocumentStatus,DocumentStorage,DocumentValidator,stable_document_id
from .cnil_discovery import CnilDiscoveryEntry,discover_metadata
from .cnil_metadata import CNIL_CANONICAL_DOMAIN,CNIL_CONNECTOR_NAME,CnilMetadata,CnilMetadataRefusal
from .cnil_models import ParsedOfficialResource,RawOfficialResource,ResourceCandidate,ValidationResult
from .cnil_catalog import CNIL_ALLOWED_DOMAINS,CNIL_CATALOG_DESCRIPTION,CNIL_DOCUMENT_FAMILIES,CNIL_PLANNED_CAPABILITIES
from .cnil_contract import CNIL_DOCUMENT_CONTRACT,CnilDocumentRegistryPort
from .cnil_models import CnilConnectorParameters
from .cnil_platform import CNIL_ACTIVATION_SCOPE,CNIL_CAPABILITIES,CNIL_DISCOVERY_LIMITS,CNIL_HEALTH,CNIL_METADATA_DISCOVERY_CAPABILITIES,CNIL_METRICS,CNIL_PLATFORM_CONTRACT,CNIL_PLATFORM_REGISTRY,CNIL_PLATFORM_VALIDATION,CNIL_STATISTICS,network_not_implemented

class CnilConnectorContract(Protocol):
 def discover_resources(self,query_or_scope:str)->list[ResourceCandidate]:...
 def fetch_resource(self,candidate:ResourceCandidate)->RawOfficialResource:...
 def validate_resource(self,raw:RawOfficialResource)->ValidationResult:...
 def parse_resource(self,raw:RawOfficialResource)->ParsedOfficialResource:...

class CnilConnector:
 platform_contract=CNIL_PLATFORM_CONTRACT
 platform_registry=CNIL_PLATFORM_REGISTRY
 platform_validation=CNIL_PLATFORM_VALIDATION
 capabilities=CNIL_CAPABILITIES
 health=CNIL_HEALTH
 statistics=CNIL_STATISTICS
 metrics=CNIL_METRICS
 enabled=platform_contract.enabled
 connector_status=platform_contract.state.value
 document_contract=CNIL_DOCUMENT_CONTRACT
 description=CNIL_CATALOG_DESCRIPTION
 allowed_domains=CNIL_ALLOWED_DOMAINS
 document_families=CNIL_DOCUMENT_FAMILIES
 planned_capabilities=CNIL_PLANNED_CAPABILITIES
 metadata_discovery_activable=True
 activation_scope=CNIL_ACTIVATION_SCOPE
 metadata_discovery_capabilities=CNIL_METADATA_DISCOVERY_CAPABILITIES
 discovery_limits=CNIL_DISCOVERY_LIMITS
 def __init__(self,*,registry:CnilDocumentRegistryPort|None=None,enabled:bool=False,mode:str="METADATA_ONLY",limit:int=50,document_registry:CnilDocumentRegistryPort|None=None,parameters:CnilConnectorParameters|None=None):
  if registry is not None and document_registry is not None:raise ValueError("configure exactly one registry")
  if parameters is not None:
   if not isinstance(parameters,CnilConnectorParameters):raise TypeError("parameters must be CnilConnectorParameters")
   if enabled is not False or mode!="METADATA_ONLY":raise ValueError("parameters cannot be combined with activation arguments")
   enabled=parameters.enabled;mode=parameters.mode
  self.parameters=CnilConnectorParameters(enabled=enabled,mode=mode)
  if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=100:raise ValueError("limit must be between 1 and 100")
  self.enabled=enabled;self.limit=limit
  self.document_registry=registry if registry is not None else document_registry
 @property
 def document_registry_compatible(self)->bool:return True
 def activate_metadata_discovery(self)->"CnilConnector":
  return type(self)(registry=self.document_registry,enabled=True,mode="METADATA_ONLY",limit=self.limit)
 def discover_metadata(self,entries:tuple[CnilDiscoveryEntry,...])->tuple[CnilMetadata,...]:
  return discover_metadata(entries,enabled=self.enabled,limit=self.limit)
 def register_discovered_metadata(self,entries:tuple[CnilDiscoveryEntry,...])->tuple[DocumentChange,...]:
  if self.document_registry is None:raise CnilMetadataRefusal("REGISTRY_NOT_CONFIGURED","Document Registry must be explicitly injected.")
  metadata=self.discover_metadata(entries);changes=[]
  for item in metadata:
   document_id=stable_document_id(CNIL_CONNECTOR_NAME,item.canonical_url)
   previous=self.document_registry.find_document(document_id)
   record=DocumentRecord(
    document_id=document_id,connector_name=CNIL_CONNECTOR_NAME,canonical_url=item.canonical_url,title=item.title,
    category=item.category.value,family=item.family.value,document_type=item.document_type.value,
    publication_date=item.publication_date,first_seen=previous.first_seen if previous else item.discovered_at,
    last_checked=item.discovered_at,last_modified_metadata=previous.last_modified_metadata if previous else item.discovered_at,
    language=item.language,provenance=item.provenance,status=previous.status if previous else DocumentStatus.ACTIVE,
   )
   changes.append(self.document_registry.update_document(record) if previous else self.document_registry.register_document(record))
  return tuple(changes)
 def discover_resources(self,_query_or_scope:str)->list[ResourceCandidate]:raise network_not_implemented()
 def fetch_resource(self,_candidate:ResourceCandidate)->RawOfficialResource:raise network_not_implemented()
 def validate_resource(self,_raw:RawOfficialResource)->ValidationResult:raise network_not_implemented()
 def parse_resource(self,_raw:RawOfficialResource)->ParsedOfficialResource:raise network_not_implemented()

def build_cnil_document_registry(storage:DocumentStorage)->DocumentRegistry:
 return DocumentRegistry(storage,DocumentValidator({CNIL_CONNECTOR_NAME:frozenset({CNIL_CANONICAL_DOMAIN})}))
