"""Inactive CARSAT facade backed exclusively by Connector Platform."""
from typing import Protocol

from .carsat_models import CarsatDocumentIdentity
from .carsat_platform import CARSAT_CAPABILITIES,CARSAT_HEALTH,CARSAT_METRICS,CARSAT_PLATFORM_CONTRACT,CARSAT_REGISTRY,CARSAT_STATISTICS,CARSAT_VALIDATION,network_not_implemented

class CarsatConnectorContract(Protocol):
 def discover(self,scope:str)->list[CarsatDocumentIdentity]:...
 def fetch(self,identity:CarsatDocumentIdentity)->bytes:...
 def synchronize(self)->None:...

class CarsatConnector:
 platform_contract=CARSAT_PLATFORM_CONTRACT;platform_registry=CARSAT_REGISTRY;platform_validation=CARSAT_VALIDATION
 capabilities=CARSAT_CAPABILITIES;health=CARSAT_HEALTH;statistics=CARSAT_STATISTICS;metrics=CARSAT_METRICS
 enabled=platform_contract.enabled;connector_status=platform_contract.state.value
 def serialize_identity(self,identity:CarsatDocumentIdentity)->dict:return identity.to_dict()
 def deserialize_identity(self,value:dict)->CarsatDocumentIdentity:return CarsatDocumentIdentity.from_dict(value)
 def discover(self,_scope:str):raise network_not_implemented()
 def fetch(self,_identity:CarsatDocumentIdentity):raise network_not_implemented()
 def synchronize(self):raise network_not_implemented()
