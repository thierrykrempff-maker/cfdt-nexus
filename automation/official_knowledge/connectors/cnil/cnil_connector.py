"""Future transport contract. Every production operation is blocked in LOT 1A."""
from __future__ import annotations
from typing import Protocol
from .cnil_models import ParsedOfficialResource,RawOfficialResource,ResourceCandidate,ValidationResult
from .cnil_catalog import CNIL_ALLOWED_DOMAINS,CNIL_CATALOG_DESCRIPTION,CNIL_DOCUMENT_FAMILIES,CNIL_PLANNED_CAPABILITIES
from .cnil_contract import CNIL_DOCUMENT_CONTRACT,CnilDocumentRegistryPort
from .cnil_models import CnilConnectorParameters
from .cnil_platform import CNIL_CAPABILITIES,CNIL_HEALTH,CNIL_METRICS,CNIL_PLATFORM_CONTRACT,CNIL_PLATFORM_REGISTRY,CNIL_PLATFORM_VALIDATION,CNIL_STATISTICS,network_not_implemented

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
 def __init__(self,document_registry:CnilDocumentRegistryPort|None=None,parameters:CnilConnectorParameters|None=None):
  self.document_registry=document_registry;self.parameters=parameters or CnilConnectorParameters()
 @property
 def document_registry_compatible(self)->bool:return True
 def discover_resources(self,_query_or_scope:str)->list[ResourceCandidate]:raise network_not_implemented()
 def fetch_resource(self,_candidate:ResourceCandidate)->RawOfficialResource:raise network_not_implemented()
 def validate_resource(self,_raw:RawOfficialResource)->ValidationResult:raise network_not_implemented()
 def parse_resource(self,_raw:RawOfficialResource)->ParsedOfficialResource:raise network_not_implemented()
