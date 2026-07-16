from dataclasses import dataclass
from enum import StrEnum

class ScheduleFrequency(StrEnum):MANUAL="manual"; DAILY="daily"; WEEKLY="weekly"; MONTHLY="monthly"; NEVER="never"; ON_EVENT="on_event"
@dataclass(frozen=True)
class SchedulePolicy:
 frequency:ScheduleFrequency=ScheduleFrequency.NEVER;enabled:bool=False
 def __post_init__(self):
  if self.enabled:raise ValueError("LOT 0 scheduler cannot be enabled")
