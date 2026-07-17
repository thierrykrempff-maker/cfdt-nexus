"""Offline ANACT connector facade and future operation contract."""
from dataclasses import dataclass
from typing import Protocol

from automation.connector_platform.connector_health import HealthReport
from automation.connector_platform.connector_provenance import Provenance

from .anact_catalog import SOURCES,get_source
from .anact_models import AnactResource,AnactSource
from .anact_platform import ANACT_CAPABILITIES,ANACT_HEALTH,ANACT_METRICS,ANACT_PLATFORM_CONTRACT,ANACT_REGISTRY,ANACT_STATISTICS,ANACT_VALIDATION,operation_not_implemented

@dataclass(frozen=True)
class ResourceValidation:
 valid:bool;errors:tuple[str,...]=()

class AnactConnectorContract(Protocol):
 def list_sources(self)->tuple[AnactSource,...]:...
 def discover(self,source_id:str)->list[AnactResource]:...
 def fetch(self,resource_id:str)->bytes:...
 def normalize(self,resource:AnactResource)->AnactResource:...
 def validate_resource(self,resource:AnactResource)->ResourceValidation:...
 def trace(self,resource:AnactResource)->Provenance:...
 def diagnose(self)->HealthReport:...
 def synchronize(self)->None:...

class AnactConnector:
 connector_id="anact";platform_contract=ANACT_PLATFORM_CONTRACT;platform_registry=ANACT_REGISTRY;platform_validation=ANACT_VALIDATION
 capabilities=ANACT_CAPABILITIES;health=ANACT_HEALTH;statistics=ANACT_STATISTICS;metrics=ANACT_METRICS
 enabled=platform_contract.enabled;connector_status=platform_contract.state.value
 def list_sources(self)->tuple[AnactSource,...]:return SOURCES
 def normalize(self,resource:AnactResource)->AnactResource:return resource
 def validate_resource(self,resource:AnactResource)->ResourceValidation:
  errors=[]
  try:get_source(resource.source_id)
  except KeyError:errors.append("unknown_source")
  if not resource.synthetic_only:errors.append("lot_0_requires_synthetic_resource")
  if resource.official_content:errors.append("official_content_forbidden")
  return ResourceValidation(not errors,tuple(errors))
 def trace(self,resource:AnactResource)->Provenance:return resource.provenance()
 def diagnose(self)->HealthReport:return self.health
 def discover(self,_source_id:str):raise operation_not_implemented()
 def fetch(self,_resource_id:str):raise operation_not_implemented()
 def synchronize(self):raise operation_not_implemented()
