from dataclasses import dataclass
from enum import StrEnum

class CacheMode(StrEnum):FORBIDDEN="forbidden"; TEMPORARY="temporary"; PERMANENT="permanent"
@dataclass(frozen=True)
class CachePolicy:
 mode:CacheMode=CacheMode.FORBIDDEN;ttl_seconds:int|None=None
 def __post_init__(self):
  if self.mode is CacheMode.FORBIDDEN and self.ttl_seconds is not None:raise ValueError("forbidden cache has no ttl")
  if self.mode is not CacheMode.FORBIDDEN and (self.ttl_seconds is None or self.ttl_seconds<=0):raise ValueError("cache ttl required")
