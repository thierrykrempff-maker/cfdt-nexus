"""Synthetic synchronization journal models."""
from dataclasses import asdict,dataclass,field
from datetime import datetime
SYNC_STATUSES={"planned","blocked","running","completed","completed_with_warnings","failed","cancelled"}
@dataclass
class SyncRun:
    sync_run_id:str; source_id:str; connector_id:str; started_at:datetime|None=None; finished_at:datetime|None=None; status:str="planned"
    requests_attempted:int=0; requests_succeeded:int=0; requests_failed:int=0; items_discovered:int=0; items_created:int=0; items_updated:int=0
    items_unchanged:int=0; items_rejected:int=0; bytes_downloaded:int=0; rate_limit_events:int=0
    errors:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); connector_version:str="architecture-only"
    def __post_init__(self):
        if self.status not in SYNC_STATUSES: raise ValueError("invalid sync status")
    def to_dict(self):return asdict(self)
