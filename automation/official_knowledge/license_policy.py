"""Conservative, explicit capabilities for supported licenses."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LicenseCapabilities:
 license_id:str;full_text_allowed:bool;cache_allowed:bool;permanent_storage_allowed:bool;indexing_allowed:bool
 fulltext_indexing_allowed:bool;metadata_indexing_allowed:bool;excerpt_retention_allowed:bool;max_excerpt_chars:int
 citation_required:bool;attribution_required:bool;transformation_allowed:bool;redistribution_allowed:bool;legal_review_required:bool

def _c(name,full,cache,permanent,index,fullindex,metadata,excerpt,maxchars,cite,attrib,transform,redistribute,review):
 return LicenseCapabilities(name,full,cache,permanent,index,fullindex,metadata,excerpt,maxchars,cite,attrib,transform,redistribute,review)

LICENSE_POLICIES={
 "LICENCE_OUVERTE":_c("LICENCE_OUVERTE",True,True,True,True,True,True,True,1000,True,True,True,True,False),
 "CC_BY":_c("CC_BY",True,True,True,True,True,True,True,1000,True,True,True,True,False),
 "CC_BY_SA":_c("CC_BY_SA",True,True,True,True,True,True,True,1000,True,True,True,True,True),
 "CC_BY_ND":_c("CC_BY_ND",True,True,True,True,False,True,True,300,True,True,False,True,True),
 "CC_BY_NC":_c("CC_BY_NC",True,True,False,True,False,True,True,500,True,True,True,False,True),
 "CC_BY_NC_SA":_c("CC_BY_NC_SA",True,True,False,True,False,True,True,500,True,True,True,False,True),
 "CC_BY_NC_ND":_c("CC_BY_NC_ND",False,True,False,True,False,True,True,200,True,True,False,False,True),
 "PUBLIC_DOMAIN":_c("PUBLIC_DOMAIN",True,True,True,True,True,True,True,1000,False,False,True,True,False),
 "UNKNOWN":_c("UNKNOWN",False,False,False,False,False,True,False,0,True,True,False,False,True),
}
ALIASES={"Licence Ouverte":"LICENCE_OUVERTE","CC BY":"CC_BY","CC BY-SA":"CC_BY_SA","CC BY-ND":"CC_BY_ND","CC BY-NC":"CC_BY_NC","CC BY-NC-SA":"CC_BY_NC_SA","CC BY-NC-ND":"CC_BY_NC_ND","Domaine Public":"PUBLIC_DOMAIN","inconnue":"UNKNOWN"}

def license_capabilities(license_id:str)->LicenseCapabilities:
 return LICENSE_POLICIES.get(ALIASES.get(license_id,license_id),LICENSE_POLICIES["UNKNOWN"])
