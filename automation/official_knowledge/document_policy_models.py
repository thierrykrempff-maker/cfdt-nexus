"""Shared immutable models for Official Knowledge document policy LOT 1B."""
from __future__ import annotations
from dataclasses import asdict,dataclass,field
from datetime import datetime
from enum import Enum

class IndexLevel(str,Enum):
 NONE="NONE";METADATA_ONLY="METADATA_ONLY";EXCERPTS="EXCERPTS";FULLTEXT_ALLOWED="FULLTEXT_ALLOWED";INTERNE_ONLY="INTERNE_ONLY"
class CacheMode(str,Enum):
 FORBIDDEN="forbidden";TEMPORARY="temporary";PERMANENT="permanent"
class RefreshMode(str,Enum):
 MANUAL="manual";DAILY="daily";WEEKLY="weekly";MONTHLY="monthly";NEVER="never";ON_EVENT="on_event"
class CitationBasis(str,Enum):
 METADATA_ONLY="metadata_only";EXCERPT="excerpt";INTERNAL_DOCUMENT="internal_document";MULTIPLE_SOURCES="multiple_sources"
class VersionState(str,Enum):
 CURRENT="current";HISTORICAL="historical";DELETED="deleted";UNCHANGED="unchanged";NEW_VERSION="new_version"

@dataclass(frozen=True)
class DocumentIdentity:
 document_id:str;source_id:str;canonical_uri:str;provenance_id:str;license_id:str;authority_level:str
 published_at:datetime|None=None;modified_at:datetime|None=None;version_id:str|None=None;content_sha256:str|None=None;schema_version:str="1.0"
 def __post_init__(self):
  if not self.provenance_id or not self.license_id:raise ValueError("provenance and license are mandatory")

@dataclass(frozen=True)
class CitationSource:
 source_id:str;title:str;canonical_uri:str;provenance_id:str;license_id:str;authority_level:str
 retrieved_at:datetime|None=None;version_id:str|None=None;excerpt:str|None=None;internal:bool=False

@dataclass(frozen=True)
class CitationRecord:
 citation_id:str;basis:CitationBasis;sources:tuple[CitationSource,...];created_at:datetime;warnings:tuple[str,...]=()
 def __post_init__(self):
  if not self.sources:raise ValueError("citation requires at least one source")
 def to_dict(self):return asdict(self)

@dataclass(frozen=True)
class DeletionDecision:
 allowed:bool;reason:str;preserve_artifacts:tuple[str,...]=("sync_journal","provenance","fingerprint")

@dataclass(frozen=True)
class PolicyDecision:
 allowed:bool;reason:str;requirements:tuple[str,...]=();warnings:tuple[str,...]=()
