"""Pure rate-limit calculations; this module never sleeps."""
from dataclasses import dataclass

@dataclass(frozen=True)
class RateLimitPolicy:
    max_requests_per_minute:int=30; minimum_delay_seconds:float=2.0; backoff_factor:float=2.0
    max_attempts:int=3; respect_retry_after:bool=True; daily_limit:int|None=None; stop_after_repeated_errors:int=5
    def __post_init__(self):
        if self.max_requests_per_minute<1 or self.max_attempts<1: raise ValueError("invalid rate limit")
def minimum_interval(policy:RateLimitPolicy)->float:return max(policy.minimum_delay_seconds,60/policy.max_requests_per_minute)
def backoff_seconds(policy:RateLimitPolicy,attempt:int,retry_after:float|None=None)->float:
    calculated=policy.minimum_delay_seconds*(policy.backoff_factor**max(0,attempt-1))
    return max(calculated,retry_after or 0) if policy.respect_retry_after else calculated
def should_stop(policy:RateLimitPolicy,attempt:int,repeated_errors:int,daily_count:int=0)->bool:
    return attempt>=policy.max_attempts or repeated_errors>=policy.stop_after_repeated_errors or policy.daily_limit is not None and daily_count>=policy.daily_limit
