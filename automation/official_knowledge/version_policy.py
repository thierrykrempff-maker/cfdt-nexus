"""Version comparison based on deterministic fingerprints."""
from __future__ import annotations
from dataclasses import dataclass
from .document_policy_models import VersionState
from .fingerprints import content_sha256,version_id

@dataclass(frozen=True)
class VersionDecision:
 state:VersionState;content_sha256:str;version_id:str;previous_version_id:str|None=None

def compare_version(source_id:str,uri:str,content:bytes|str,previous_hash:str|None=None,previous_version_id:str|None=None)->VersionDecision:
 digest=content_sha256(content);vid=version_id(source_id,uri,digest)
 state=VersionState.UNCHANGED if previous_hash==digest else VersionState.NEW_VERSION
 return VersionDecision(state,digest,vid,previous_version_id)
def mark_current(decision:VersionDecision)->VersionDecision:return VersionDecision(VersionState.CURRENT,decision.content_sha256,decision.version_id,decision.previous_version_id)
def mark_historical(decision:VersionDecision)->VersionDecision:return VersionDecision(VersionState.HISTORICAL,decision.content_sha256,decision.version_id,decision.previous_version_id)
