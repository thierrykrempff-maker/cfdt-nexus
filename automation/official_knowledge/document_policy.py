"""Composition root for the shared official-document policy."""
from __future__ import annotations
from dataclasses import dataclass
from .document_cache_policy import CachePolicy,allow_cache
from .document_policy_models import IndexLevel,PolicyDecision
from .index_policy import decide_index
from .license_policy import license_capabilities

@dataclass(frozen=True)
class DocumentPolicy:
 license_id:str;index_level:IndexLevel;cache_policy:CachePolicy;authority_level:str;require_provenance:bool=True

def evaluate_document(policy:DocumentPolicy,*,has_provenance:bool,internal:bool=False)->dict[str,PolicyDecision]:
 cap=license_capabilities(policy.license_id)
 provenance=PolicyDecision(has_provenance or not policy.require_provenance,"PROVENANCE_PRESENT" if has_provenance else "PROVENANCE_REQUIRED")
 index=decide_index(policy.index_level,cap,internal=internal)
 cache=allow_cache(policy.cache_policy,cap)
 if not provenance.allowed:
  index=PolicyDecision(False,"PROVENANCE_REQUIRED");cache=PolicyDecision(False,"PROVENANCE_REQUIRED")
 return {"provenance":provenance,"index":index,"cache":cache}
