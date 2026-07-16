"""Retention and deletion rules preserving immutable audit evidence."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timedelta
from .document_policy_models import DeletionDecision

PROTECTED_ARTIFACTS=frozenset({"sync_journal","provenance","fingerprint"})
@dataclass(frozen=True)
class RetentionPolicy:
 retain_for:timedelta|None;delete_expired_content:bool=False;retain_history:bool=True

def deletion_decision(artifact_type:str,*,now:datetime,created_at:datetime,policy:RetentionPolicy)->DeletionDecision:
 if artifact_type in PROTECTED_ARTIFACTS:return DeletionDecision(False,"PROTECTED_AUDIT_ARTIFACT")
 if not policy.delete_expired_content:return DeletionDecision(False,"DELETION_DISABLED")
 if policy.retain_for is None or now<created_at+policy.retain_for:return DeletionDecision(False,"RETENTION_ACTIVE")
 return DeletionDecision(True,"POLICY_EXPIRY_REACHED")
