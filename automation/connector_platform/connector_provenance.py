from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Provenance:
 source_id:str;canonical_url:str;retrieved_at:datetime|None;fingerprint:str|None
 def __post_init__(self):
  if not self.source_id or not self.canonical_url.startswith("https://"):raise ValueError("invalid provenance")
  if self.retrieved_at is not None and self.retrieved_at.tzinfo is None:raise ValueError("timezone required")
