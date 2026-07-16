"""Indexing decisions bounded by connector declaration and license."""
from __future__ import annotations
from .document_policy_models import IndexLevel,PolicyDecision
from .license_policy import LicenseCapabilities

def decide_index(level:IndexLevel,license_policy:LicenseCapabilities,*,internal:bool=False)->PolicyDecision:
 if level==IndexLevel.NONE:return PolicyDecision(False,"INDEX_DISABLED")
 if level==IndexLevel.INTERNE_ONLY:return PolicyDecision(internal,"INTERNAL_DOCUMENT" if internal else "EXTERNAL_NOT_ALLOWED")
 if level==IndexLevel.METADATA_ONLY:return PolicyDecision(license_policy.metadata_indexing_allowed,"METADATA_ALLOWED" if license_policy.metadata_indexing_allowed else "LICENSE_REFUSED")
 if level==IndexLevel.EXCERPTS:return PolicyDecision(license_policy.indexing_allowed and license_policy.excerpt_retention_allowed,"EXCERPTS_ALLOWED" if license_policy.excerpt_retention_allowed else "EXCERPTS_REFUSED",("provenance","license","version"))
 allowed=license_policy.indexing_allowed and license_policy.fulltext_indexing_allowed
 return PolicyDecision(allowed,"FULLTEXT_ALLOWED" if allowed else "FULLTEXT_INDEXING_REFUSED",("provenance","license","version"))

def connector_level(level:str)->IndexLevel:return IndexLevel(level)
