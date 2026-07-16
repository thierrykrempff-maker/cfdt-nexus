from dataclasses import dataclass
from datetime import datetime,timezone

def utc_now()->datetime:return datetime.now(timezone.utc)

@dataclass(frozen=True)
class OperationContext:
 connector_id:str;operation_id:str;created_at:datetime
 def __post_init__(self):
  if not self.connector_id or not self.operation_id or self.created_at.tzinfo is None:raise ValueError("invalid operation context")

@dataclass(frozen=True)
class OperationResult:
 success:bool;code:str;message:str;document_count:int=0
 def __post_init__(self):
  if not self.code or self.document_count<0:raise ValueError("invalid operation result")
