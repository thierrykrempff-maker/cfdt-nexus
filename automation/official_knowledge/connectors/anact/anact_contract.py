"""Offline ANACT connector facade and future operation contract."""
from dataclasses import dataclass
from typing import Protocol

from automation.connector_platform.connector_health import HealthReport
from automation.connector_platform.connector_provenance import Provenance

from .anact_catalog import SOURCES,get_source
from .anact_classification_models import UrlClassification
from .anact_document_catalog import InMemoryAnactDocumentCatalog
from .anact_freshness import FRESHNESS_POLICIES,FreshnessPolicy
from .anact_legal_policy import ANACT_LEGAL_POLICY,LegalPolicy
from .anact_models import AnactResource,AnactSource
from .anact_page_metadata_models import PageMetadataResult,PageMetadataTarget
from .anact_page_metadata_transport import AnactPageMetadataTransport
from .anact_review_queue import AnactReviewQueue
from .anact_source_audit import AUDIT_RECORDS,SourceAuditRecord
from .anact_sitemap_transport import AnactSitemapTransport
from .anact_transport_models import ConditionalState,SitemapCandidate,SitemapInspectionResult
from .anact_url_classifier import AnactUrlClassifier
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
 sitemap_transport_implemented=True;sitemap_transport_enabled_by_default=False
 page_metadata_transport_implemented=True;page_metadata_transport_enabled_by_default=False
 def list_sources(self)->tuple[AnactSource,...]:return SOURCES
 def source_audit(self)->tuple[SourceAuditRecord,...]:return AUDIT_RECORDS
 def legal_policy(self)->LegalPolicy:return ANACT_LEGAL_POLICY
 def freshness_policies(self)->tuple[FreshnessPolicy,...]:return FRESHNESS_POLICIES
 def inspect_sitemap(self,transport:AnactSitemapTransport,state:ConditionalState=ConditionalState())->SitemapInspectionResult:return transport.inspect(state)
 def classify_candidate(self,candidate:SitemapCandidate)->UrlClassification:return AnactUrlClassifier().classify_candidate(candidate)
 def classify_candidates(self,candidates:tuple[SitemapCandidate,...])->tuple[UrlClassification,...]:return AnactUrlClassifier().classify_candidates(candidates)
 def new_review_queue(self)->AnactReviewQueue:return AnactReviewQueue()
 def new_document_catalog(self)->InMemoryAnactDocumentCatalog:return InMemoryAnactDocumentCatalog()
 def read_page_metadata(self,target:PageMetadataTarget,transport:AnactPageMetadataTransport,state:ConditionalState=ConditionalState())->PageMetadataResult:return transport.inspect(target,state)
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
