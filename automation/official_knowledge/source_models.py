"""Static official-source definitions."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field

SOURCE_TYPES = {"official_api","open_data","rss_or_feed","targeted_pages","downloadable_dataset","existing_internal_connector","unknown"}
CONNECTOR_STATUSES = {"not_investigated","architecture_only","pending_authorization","implemented","disabled","deprecated"}

@dataclass(frozen=True)
class SourceDefinition:
    source_id: str; display_name: str; publisher: str; source_type: str = "unknown"
    official_domains: tuple[str,...] = (); allowed_access_modes: tuple[str,...] = ()
    authority_level: str = "unknown"; domain_tags: tuple[str,...] = ()
    default_refresh_policy: str = "pending_review"; rate_limit_policy: str = "default_disabled"
    license_status: str = "not_reviewed"; terms_review_status: str = "pending_review"
    enabled: bool = False; kill_switch_key: str = ""; connector_status: str = "architecture_only"
    notes: str = "Verification required before authorization."; schema_version: str = "1.0"
    def __post_init__(self):
        if self.source_type not in SOURCE_TYPES: raise ValueError("invalid source_type")
        if self.connector_status not in CONNECTOR_STATUSES: raise ValueError("invalid connector_status")
    def to_dict(self): return asdict(self)
