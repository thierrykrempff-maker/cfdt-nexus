"""Data-only future response contract; it does not render an employee answer."""
from dataclasses import dataclass

@dataclass(frozen=True)
class FutureLocalLawSection:
    trigger_reason:str; applicability_status:str; local_provision:str|None
    common_law_comparison:str|None; collective_comparison:str|None
    practical_consequence:str|None; confidence:str; missing_information:tuple[str,...]
    official_source_ids:tuple[str,...]
