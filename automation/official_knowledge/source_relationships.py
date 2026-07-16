"""Typed relationships that never imply institutional sources replace law."""
from __future__ import annotations
from .catalog_models import SourceRelationship

RELATION_TYPES=frozenset({"supersedes","complements","practical_explanation_of","authoritative_version_of","dataset_from","regional_instance_of","employer_position_on","technical_reference_for","duplicate_scope_with"})
RELATIONSHIPS=(
 SourceRelationship("dreets_grand_est","regional_instance_of","dreets_national"),
 SourceRelationship("dreal_grand_est","regional_instance_of","dreal_national"),
 SourceRelationship("service_public","practical_explanation_of","legifrance"),
 SourceRelationship("code_travail_numerique","practical_explanation_of","legifrance"),
 SourceRelationship("aida","technical_reference_for","icpe_legal_sources"),
 SourceRelationship("aria","technical_reference_for","industrial_accident_feedback"),
 SourceRelationship("legifrance","authoritative_version_of","french_legal_texts"),
 SourceRelationship("france_chimie","employer_position_on","chemical_industry_branch"),
 SourceRelationship("gestis","complements","echa"),
 SourceRelationship("data_gouv_fr","dataset_from","registered_public_publishers"),
)

def validate_relationships(source_ids:set[str])->None:
 for relation in RELATIONSHIPS:
  if relation.relation_type not in RELATION_TYPES: raise ValueError("invalid relationship")
  if relation.subject_id not in source_ids: raise ValueError("unknown relationship subject")
  if relation.relation_type in {"supersedes","authoritative_version_of"} and relation.subject_id==relation.object_id: raise ValueError("self authority cycle")
 graph={r.subject_id:r.object_id for r in RELATIONSHIPS if r.relation_type=="supersedes"}
 for start in graph:
  seen=set();node=start
  while node in graph:
   if node in seen: raise ValueError("supersedes cycle")
   seen.add(node);node=graph[node]
