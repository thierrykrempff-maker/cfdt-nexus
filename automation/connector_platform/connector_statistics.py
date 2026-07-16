from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class ConnectorStatistics:
 document_count:int=0;consultation_count:int=0;average_duration_ms:float=0
 last_synchronization:datetime|None=None;last_validation:datetime|None=None
 def __post_init__(self):
  if min(self.document_count,self.consultation_count,self.average_duration_ms)<0:raise ValueError("statistics cannot be negative")
