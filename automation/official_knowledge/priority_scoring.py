"""Development scoring is deterministic and distinct from legal authority."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ScoreFactors:
 legal_authority:int;employee_daily_utility:int;representative_utility:int
 seveso_relevance:int;regional_relevance:int;source_quality:int;technical_feasibility:int;license_clarity:int
 def __post_init__(self):
  limits=(25,15,15,20,10,5,5,5)
  for value,limit in zip(self.__dict__.values(),limits):
   if not 0<=value<=limit: raise ValueError("score factor outside range")

def development_score(factors:ScoreFactors)->int:
 return sum(factors.__dict__.values())
