from dataclasses import dataclass

@dataclass(frozen=True)
class Metric:
 name:str;value:float;unit:str
 def __post_init__(self):
  if not self.name or not self.unit:raise ValueError("invalid metric")
