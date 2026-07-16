from dataclasses import dataclass,field
from .connector_contract import ConnectorContract

@dataclass
class ConnectorRegistry:
 _items:dict[str,ConnectorContract]=field(default_factory=dict)
 def register(self,contract:ConnectorContract)->None:
  key=contract.metadata.connector_id
  if key in self._items:raise ValueError("duplicate connector")
  self._items[key]=contract
 def get(self,connector_id:str)->ConnectorContract:return self._items[connector_id]
 def list_ids(self)->tuple[str,...]:return tuple(sorted(self._items))
