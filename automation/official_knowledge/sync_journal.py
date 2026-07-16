"""In-memory/synthetic journal only; no network or mandatory disk output."""
from __future__ import annotations
import uuid
from .sync_models import SyncRun

def stable_sync_id(source_id:str,connector_id:str,planned_key:str)->str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL,f"cfdt-nexus:official-sync:{source_id}:{connector_id}:{planned_key}"))
def planned_run(source_id:str,connector_id:str,planned_key:str)->SyncRun:
    return SyncRun(stable_sync_id(source_id,connector_id,planned_key),source_id,connector_id,status="planned")
def blocked_run(source_id:str,connector_id:str,planned_key:str,reason:str="NETWORK_DISABLED_BY_DEFAULT")->SyncRun:
    run=planned_run(source_id,connector_id,planned_key);run.status="blocked";run.errors.append(reason);return run
