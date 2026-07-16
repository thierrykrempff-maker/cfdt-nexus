"""Static source-catalog models. Catalog presence never authorizes access."""
from __future__ import annotations
from dataclasses import asdict, dataclass

PUBLISHER_TYPES=frozenset({"government","public_authority","court","public_agency","social_security_body","european_institution","international_institution","public_research_body","employer_federation","trade_union","joint_body","training_body","professional_observatory","foreign_public_institution","unknown"})
INSTITUTIONAL_POSITIONS=frozenset({"neutral_public_authority","legislative_or_regulatory_authority","judicial_authority","official_guidance_provider","prevention_body","social_security_operator","employer_side_institution","employee_side_institution","joint_governance","technical_reference_body","unknown"})
PRIORITY_LEVELS=tuple(f"PRIORITY_{index}" for index in range(7))
DEVELOPMENT_WAVES=tuple(f"WAVE_{index}" for index in range(5))

@dataclass(frozen=True)
class CatalogSource:
 source_id:str;display_name:str;publisher:str;publisher_type:str;institutional_position:str
 jurisdiction:str;geographic_scope:tuple[str,...];source_type:str;authority_level:str
 nexus_priority_level:str;nexus_priority_rank:int;primary_domains:tuple[str,...];secondary_domains:tuple[str,...]=()
 topic_tags:tuple[str,...]=();target_engines:tuple[str,...]=();relevance_for_ineos_sarralbe:str="medium"
 relevance_for_cssct:str="medium";relevance_for_cse:str="medium";relevance_for_payroll:str="low"
 relevance_for_protection_sociale:str="low";official_domains:tuple[str,...]=();possible_access_modes:tuple[str,...]=()
 access_review_status:str="not_reviewed";license_review_status:str="not_reviewed";document_policy_id:str="fail_closed_default"
 connector_status:str="not_investigated";enabled:bool=False;dependency_sources:tuple[str,...]=();overlap_with_sources:tuple[str,...]=()
 development_wave:str="WAVE_4";development_rank:int=999;selection_reason:str="Catalogue review required."
 caveats:tuple[str,...]=();schema_version:str="1.0"
 def __post_init__(self):
  if self.publisher_type not in PUBLISHER_TYPES: raise ValueError("invalid publisher_type")
  if self.institutional_position not in INSTITUTIONAL_POSITIONS: raise ValueError("invalid institutional_position")
  if self.nexus_priority_level not in PRIORITY_LEVELS: raise ValueError("invalid priority")
  if self.development_wave not in DEVELOPMENT_WAVES: raise ValueError("invalid wave")
  if self.enabled: raise ValueError("catalog sources must remain disabled")
 def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class SourceRelationship:
 subject_id:str;relation_type:str;object_id:str;note:str=""
