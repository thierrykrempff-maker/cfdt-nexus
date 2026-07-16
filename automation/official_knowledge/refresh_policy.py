"""Pure refresh scheduling; no waiting or network operations."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timedelta
from .document_policy_models import RefreshMode

@dataclass(frozen=True)
class RefreshPolicy:
 mode:RefreshMode;event_name:str|None=None
 def __post_init__(self):
  if self.mode==RefreshMode.ON_EVENT and not self.event_name:raise ValueError("event refresh needs event_name")

_DELAYS={RefreshMode.DAILY:timedelta(days=1),RefreshMode.WEEKLY:timedelta(days=7),RefreshMode.MONTHLY:timedelta(days=30)}
def next_refresh(last_refresh:datetime|None,policy:RefreshPolicy)->datetime|None:
 if policy.mode in {RefreshMode.NEVER,RefreshMode.MANUAL,RefreshMode.ON_EVENT} or last_refresh is None:return None
 return last_refresh+_DELAYS[policy.mode]
def refresh_due(now:datetime,last_refresh:datetime|None,policy:RefreshPolicy,*,event:str|None=None)->bool:
 if policy.mode==RefreshMode.NEVER:return False
 if policy.mode==RefreshMode.MANUAL:return False
 if policy.mode==RefreshMode.ON_EVENT:return event==policy.event_name
 target=next_refresh(last_refresh,policy);return target is None or now>=target
