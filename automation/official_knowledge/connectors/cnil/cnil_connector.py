"""Future transport contract. Every production operation is blocked in LOT 1A."""
from __future__ import annotations
from typing import Protocol
from .cnil_models import ParsedOfficialResource,RawOfficialResource,ResourceCandidate,ValidationResult
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
 def discover_resources(self,_query_or_scope:str)->list[ResourceCandidate]:raise network_not_implemented()
 def fetch_resource(self,_candidate:ResourceCandidate)->RawOfficialResource:raise network_not_implemented()
 def validate_resource(self,_raw:RawOfficialResource)->ValidationResult:raise network_not_implemented()
 def parse_resource(self,_raw:RawOfficialResource)->ParsedOfficialResource:raise network_not_implemented()
