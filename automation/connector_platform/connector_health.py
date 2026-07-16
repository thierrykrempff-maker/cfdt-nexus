from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class HealthStatus(StrEnum):UNKNOWN="unknown"; HEALTHY="healthy"; DEGRADED="degraded"; UNAVAILABLE="unavailable"; DISABLED="disabled"
@dataclass(frozen=True)
class HealthReport:
 status:HealthStatus;checked_at:datetime;details:str=""
 def __post_init__(self):
  if self.checked_at.tzinfo is None:raise ValueError("timezone required")
