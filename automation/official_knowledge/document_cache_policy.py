"""Cache policy including validation, expiry and purge decisions."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timedelta
from .document_policy_models import CacheMode,PolicyDecision
from .license_policy import LicenseCapabilities

@dataclass(frozen=True)
class CachePolicy:
 mode:CacheMode;duration:timedelta|None;require_validation:bool=True;use_etag:bool=True;use_last_modified:bool=True;purge_on_expiry:bool=True
 def __post_init__(self):
  if self.mode==CacheMode.TEMPORARY and (self.duration is None or self.duration.total_seconds()<=0):raise ValueError("temporary cache needs duration")
  if self.mode==CacheMode.FORBIDDEN and self.duration is not None:raise ValueError("forbidden cache has no duration")

def allow_cache(policy:CachePolicy,license_policy:LicenseCapabilities)->PolicyDecision:
 if policy.mode==CacheMode.FORBIDDEN:return PolicyDecision(False,"CACHE_FORBIDDEN")
 if not license_policy.cache_allowed:return PolicyDecision(False,"LICENSE_CACHE_REFUSED")
 if policy.mode==CacheMode.PERMANENT and not license_policy.permanent_storage_allowed:return PolicyDecision(False,"PERMANENT_STORAGE_REFUSED")
 return PolicyDecision(True,"CACHE_ALLOWED",("validation","provenance","license"))
def expires_at(stored_at:datetime,policy:CachePolicy)->datetime|None:return stored_at+policy.duration if policy.duration else None
def is_expired(now:datetime,stored_at:datetime,policy:CachePolicy)->bool:
 expiry=expires_at(stored_at,policy);return expiry is not None and now>=expiry
