"""Declarative freshness policies; no scheduler or network operation."""
from dataclasses import dataclass
from enum import StrEnum

class ResourceLifecycle(StrEnum):ACTIVE="active"; MOVED="moved"; REMOVED="removed"; ARCHIVED="archived"; UNKNOWN="unknown"

@dataclass(frozen=True)
class FreshnessPolicy:
 family_id:str;revalidate_after_days:int;method:str
 publication_date_field:str|None="published_at";updated_date_field:str|None="updated_at"
 preserve_etag:bool=True;preserve_last_modified:bool=True;preserve_fingerprint:bool=True;preserve_canonical_url:bool=True
 def __post_init__(self):
  if not self.family_id or self.revalidate_after_days<1 or self.method not in {"sitemap_metadata","conditional_metadata","manual_review"}:raise ValueError("invalid freshness policy")

FRESHNESS_POLICIES=(
 FreshnessPolicy("thematic_pages",30,"sitemap_metadata"),
 FreshnessPolicy("publications",14,"sitemap_metadata"),
 FreshnessPolicy("guides",30,"conditional_metadata"),
 FreshnessPolicy("tools",30,"sitemap_metadata"),
 FreshnessPolicy("dossiers",30,"sitemap_metadata"),
 FreshnessPolicy("studies",30,"conditional_metadata"),
 FreshnessPolicy("practical_sheets",30,"conditional_metadata"),
 FreshnessPolicy("aract_resources",30,"sitemap_metadata"),
 FreshnessPolicy("news",1,"sitemap_metadata"),
 FreshnessPolicy("events",1,"sitemap_metadata"),
 FreshnessPolicy("structured_data",90,"manual_review"),
)
FRESHNESS_BY_FAMILY={policy.family_id:policy for policy in FRESHNESS_POLICIES}
