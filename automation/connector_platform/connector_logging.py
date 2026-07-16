from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class LogEventType(StrEnum):
 CONSULTATION="consultation"; ERROR="error"; REFUSAL="refusal"; VALIDATION="validation"; SYNCHRONIZATION="synchronization"; CACHE="cache"

@dataclass(frozen=True)
class LogEntry:
 event_type:LogEventType;connector_id:str;timestamp:datetime;code:str;message:str
 def __post_init__(self):
  if not self.connector_id or self.timestamp.tzinfo is None or not self.code:raise ValueError("invalid log entry")
