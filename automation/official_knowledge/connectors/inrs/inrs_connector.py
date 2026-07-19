"""Public facade for offline INRS metadata discovery and synchronization contracts."""

from __future__ import annotations

from typing import Any, Mapping

from .inrs_contract import INRS_DOCUMENT_CONTRACT, InrsDocumentRegistryPort
from .inrs_discovery import DEFAULT_DISCOVERY_LIMIT, discover_inrs_metadata
from .inrs_metadata import InrsMetadata
from .inrs_models import InrsDocumentIdentity
from .inrs_platform import (
    INRS_CAPABILITIES, INRS_HEALTH, INRS_METRICS, INRS_OFFICIAL_DOMAINS,
    INRS_PLATFORM_CONTRACT, INRS_REGISTRY, INRS_STATISTICS, INRS_VALIDATION,
    network_not_implemented,
)


class InrsConnector:
    """Disabled-by-default metadata facade; production transport remains blocked."""

    platform_contract=INRS_PLATFORM_CONTRACT;platform_registry=INRS_REGISTRY
    platform_validation=INRS_VALIDATION;capabilities=INRS_CAPABILITIES
    health=INRS_HEALTH;statistics=INRS_STATISTICS;metrics=INRS_METRICS
    document_contract=INRS_DOCUMENT_CONTRACT;official_domains=INRS_OFFICIAL_DOMAINS
    enabled=platform_contract.enabled;connector_status=platform_contract.state.value
    def __init__(self,*,document_registry:InrsDocumentRegistryPort|None=None,enabled:bool=False,limit:int=DEFAULT_DISCOVERY_LIMIT):
        if not isinstance(enabled,bool):raise TypeError("enabled must be a boolean")
        if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=100:raise ValueError("limit must be between 1 and 100")
        self.document_registry=document_registry;self.enabled=enabled;self.limit=limit
    @property
    def document_registry_compatible(self)->bool:return True
    def serialize_identity(self,identity:InrsDocumentIdentity)->dict:return identity.to_dict()
    def deserialize_identity(self,value:dict)->InrsDocumentIdentity:return InrsDocumentIdentity.from_dict(value)
    def activate_metadata_discovery(self)->"InrsConnector":
        return type(self)(document_registry=self.document_registry,enabled=True,limit=self.limit)
    def discover_metadata(self,entries:tuple[Mapping[str,Any],...])->tuple[InrsMetadata,...]:
        return discover_inrs_metadata(entries,enabled=self.enabled,limit=self.limit)
    def discover(self,_scope:str):raise network_not_implemented()
    def fetch(self,_identity:InrsDocumentIdentity):raise network_not_implemented()
    def synchronize(self):raise network_not_implemented()
