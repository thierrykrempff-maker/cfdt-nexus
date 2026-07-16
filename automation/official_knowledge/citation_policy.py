"""Citation rules preserving provenance, license, authority, dates and version."""
from __future__ import annotations
import uuid
from datetime import datetime,timezone
from .document_policy_models import CitationBasis,CitationRecord,CitationSource
from .license_policy import license_capabilities

def build_citation(basis:CitationBasis,sources:tuple[CitationSource,...],created_at:datetime|None=None)->CitationRecord:
 if basis==CitationBasis.MULTIPLE_SOURCES and len(sources)<2:raise ValueError("multiple sources basis requires at least two sources")
 for source in sources:
  if not all((source.provenance_id,source.license_id,source.authority_level)):raise ValueError("incomplete citation traceability")
  cap=license_capabilities(source.license_id)
  if source.excerpt is not None:
   if not cap.excerpt_retention_allowed:raise ValueError("excerpt forbidden by license")
   if len(source.excerpt)>cap.max_excerpt_chars:raise ValueError("excerpt too long")
 seed="|".join(f"{s.provenance_id}:{s.version_id or ''}:{s.excerpt or ''}" for s in sources)
 cid=str(uuid.uuid5(uuid.NAMESPACE_URL,"cfdt-nexus:citation:"+basis.value+":"+seed))
 return CitationRecord(cid,basis,sources,created_at or datetime.now(timezone.utc))
