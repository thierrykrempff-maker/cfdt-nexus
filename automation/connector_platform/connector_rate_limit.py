from dataclasses import dataclass

@dataclass(frozen=True)
class RateLimitPolicy:
 requests:int;window_seconds:int
 def __post_init__(self):
  if self.requests<=0 or self.window_seconds<=0:raise ValueError("positive limits required")
 def allows(self,count:int)->bool:return 0<=count<self.requests
