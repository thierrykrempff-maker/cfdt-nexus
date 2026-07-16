"""Fail-closed license and terms model."""
from dataclasses import asdict,dataclass
from datetime import datetime

REVIEW_STATUSES={"not_reviewed","pending","approved","restricted","prohibited"}
@dataclass(frozen=True)
class LicensePolicy:
    license_id:str; license_name:str="unknown"; license_uri:str|None=None
    reuse_allowed:bool=False; redistribution_allowed:bool=False; attribution_required:bool=True
    caching_allowed:bool=False; full_text_storage_allowed:bool=False; review_status:str="not_reviewed"
    reviewed_at:datetime|None=None; notes:str="Review required before automated use."
    def __post_init__(self):
        if self.review_status not in REVIEW_STATUSES: raise ValueError("invalid review_status")
    def to_dict(self): return asdict(self)
