from dataclasses import dataclass

@dataclass(frozen=True)
class RetryPolicy:
 max_attempts:int=1;retryable_codes:frozenset[str]=frozenset()
 def __post_init__(self):
  if self.max_attempts<1:raise ValueError("at least one attempt")
 def should_retry(self,attempt:int,code:str)->bool:return attempt<self.max_attempts and code in self.retryable_codes
