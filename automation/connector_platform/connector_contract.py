from dataclasses import dataclass,field
from .connector_capabilities import Capability
from .connector_document import DocumentPolicy
from .connector_license import LicenseId
from .connector_metadata import ConnectorMetadata
from .connector_security import SecurityPolicy
from .connector_states import ConnectorState

@dataclass(frozen=True)
class ConnectorContract:
 metadata:ConnectorMetadata;state:ConnectorState=ConnectorState.ARCHITECTURE_ONLY
 capabilities:frozenset[Capability]=field(default_factory=frozenset)
 document_policy:DocumentPolicy=DocumentPolicy.METADATA_ONLY;license_id:LicenseId=LicenseId.UNKNOWN
 security:SecurityPolicy=field(default_factory=SecurityPolicy)
 enabled:bool=False
 def __post_init__(self):
  if self.enabled or self.state is ConnectorState.ENABLED:raise ValueError("LOT 0 cannot enable a connector")
  forbidden={Capability.AUTHENTICATION,Capability.SYNC,Capability.DOWNLOAD}
  if self.capabilities&forbidden:raise ValueError("active capabilities forbidden by default")
