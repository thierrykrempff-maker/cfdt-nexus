from dataclasses import dataclass

@dataclass(frozen=True)
class BackoffPolicy:
 initial_seconds:float=1.0;factor:float=2.0;maximum_seconds:float=60.0
 def __post_init__(self):
  if self.initial_seconds<=0 or self.factor<1 or self.maximum_seconds<self.initial_seconds:raise ValueError("invalid backoff")
 def delay(self,attempt:int)->float:
  if attempt<1:raise ValueError("attempt starts at one")
  return min(self.initial_seconds*(self.factor**(attempt-1)),self.maximum_seconds)
