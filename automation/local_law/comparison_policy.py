"""Conservative comparison contract: identify, scope, public policy, derogation, then review."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ComparisonRequest:
    local_rule_applies:bool|None; common_law_applies:bool|None
    collective_rule_applies:bool|None; company_rule_applies:bool|None
    same_object_confirmed:bool=False; public_policy_checked:bool=False; derogation_checked:bool=False

@dataclass(frozen=True)
class ComparisonDecision:
    local_rule_applies:bool|None; common_law_applies:bool|None; collective_rule_applies:bool|None
    company_rule_applies:bool|None; comparison_required:bool; legal_review_required:bool
    selected_rule:str|None; selection_reason:str; unresolved_conflicts:tuple[str,...]

def compare(request:ComparisonRequest)->ComparisonDecision:
    values=(request.local_rule_applies,request.common_law_applies,request.collective_rule_applies,request.company_rule_applies)
    candidates=sum(value is True for value in values)
    unresolved=[]
    if any(value is None for value in values): unresolved.append("applicability_or_text_missing")
    if candidates>1 and not request.same_object_confirmed: unresolved.append("objects_may_differ")
    if not request.public_policy_checked: unresolved.append("public_policy_not_checked")
    if not request.derogation_checked: unresolved.append("derogation_not_checked")
    review=candidates!=1 or bool(unresolved)
    selected="local" if candidates==1 and request.local_rule_applies and not unresolved else None
    reason="single_scoped_rule_after_required_checks" if selected else "no_automatic_priority_legal_comparison_required"
    return ComparisonDecision(request.local_rule_applies,request.common_law_applies,request.collective_rule_applies,request.company_rule_applies,candidates>1,review,selected,reason,tuple(unresolved))
