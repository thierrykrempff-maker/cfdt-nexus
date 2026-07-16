"""Parser contract using synthetic payloads only in LOT 1A."""
from __future__ import annotations
from automation.official_knowledge.fingerprints import content_sha256
from .cnil_models import CnilResource,ParsedOfficialResource,RawOfficialResource,stable_resource_id

def parse_synthetic_resource(raw:RawOfficialResource,*,license_id:str,license_status:str)->ParsedOfficialResource:
 text=raw.body.decode("utf-8") if raw.mime_type.startswith("text/") or raw.mime_type=="application/json" else ""
 candidate=raw.candidate
 resource=CnilResource(stable_resource_id(candidate.canonical_uri),"cnil",candidate.canonical_uri,candidate.resource_type,candidate.title,
  theme_tags=candidate.theme_tags,audience_tags=candidate.audience_tags,license_id=license_id,license_review_status=license_status,
  retrieval_mode=candidate.retrieval_mode,content_format=candidate.content_format,content_sha256=content_sha256(raw.body),
  indexable=license_status=="approved",rejection_reason=None if license_status=="approved" else "LICENSE_NOT_APPROVED",
  provenance={"source_id":"cnil","canonical_uri":candidate.canonical_uri,"confidentiality_level":"public_official"})
 return ParsedOfficialResource(resource,text)
