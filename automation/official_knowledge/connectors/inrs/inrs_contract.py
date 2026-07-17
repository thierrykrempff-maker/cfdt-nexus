from typing import Protocol
from .inrs_models import InrsDocumentIdentity
from .inrs_platform import INRS_CAPABILITIES,INRS_HEALTH,INRS_METRICS,INRS_PLATFORM_CONTRACT,INRS_REGISTRY,INRS_STATISTICS,INRS_VALIDATION,network_not_implemented

class InrsConnectorContract(Protocol):
 def discover(self,scope:str)->list[InrsDocumentIdentity]:...
 def fetch(self,identity:InrsDocumentIdentity)->bytes:...
 def synchronize(self)->None:...

class InrsConnector:
 platform_contract=INRS_PLATFORM_CONTRACT;platform_registry=INRS_REGISTRY;platform_validation=INRS_VALIDATION
 capabilities=INRS_CAPABILITIES;health=INRS_HEALTH;statistics=INRS_STATISTICS;metrics=INRS_METRICS
 enabled=platform_contract.enabled;connector_status=platform_contract.state.value
 def serialize_identity(self,identity:InrsDocumentIdentity)->dict:return identity.to_dict()
 def deserialize_identity(self,value:dict)->InrsDocumentIdentity:return InrsDocumentIdentity.from_dict(value)
 def discover(self,_scope:str):raise network_not_implemented()
 def fetch(self,_identity:InrsDocumentIdentity):raise network_not_implemented()
 def synchronize(self):raise network_not_implemented()
