"""Verified observations and prioritization; no endpoint or transport configuration."""
from .inrs_models import AccessEvidence,EvidenceStatus,FamilyProfile,InrsDocumentType,ResourceFamily

ACCESS_EVIDENCE=(
 AccessEvidence("targeted_html_pages",EvidenceStatus.OFFICIALLY_OBSERVED,notes="resource pages expose title, type, INRS reference and publication date"),
 AccessEvidence("pdf_files",EvidenceStatus.OFFICIALLY_OBSERVED,notes="downloadable formats exist but content reuse is restricted"),
 AccessEvidence("rss",EvidenceStatus.OBSERVED_NOT_VALIDATED,notes="RSS is exposed by the documentary portal; no connector use is authorized"),
 AccessEvidence("robots_txt",EvidenceStatus.OBSERVED_NOT_VALIDATED,notes="review tooling could not validate the payload"),
 AccessEvidence("xml_sitemap",EvidenceStatus.OBSERVED_NOT_VALIDATED,notes="review tooling could not validate the payload"),
 AccessEvidence("public_api",EvidenceStatus.NOT_IDENTIFIED_IN_LIMITED_REVIEW,notes="no official API or developer documentation identified"),
 AccessEvidence("openapi",EvidenceStatus.NOT_IDENTIFIED_IN_LIMITED_REVIEW,notes="no OpenAPI or Swagger documentation identified"),
 AccessEvidence("reuse_license",EvidenceStatus.LEGAL_REVIEW_REQUIRED,notes="copyright terms prohibit non-private reproduction; links are allowed under stated conditions"),
)

FAMILY_PROFILES=(
 FamilyProfile(ResourceFamily.BROCHURE,"high","medium","medium","very_high","very_high","high",1),
 FamilyProfile(ResourceFamily.PRACTICAL_SHEET,"high","medium","medium","very_high","very_high","high",1),
 FamilyProfile(ResourceFamily.DOSSIER,"high","medium","medium","very_high","very_high","high",1),
 FamilyProfile(ResourceFamily.NEWS,"medium","low","low","high","high","medium",3),
 FamilyProfile(ResourceFamily.QUESTION_ANSWER,"high","medium","medium","high","high","high",2),
 FamilyProfile(ResourceFamily.TOOL,"medium","medium","low","very_high","very_high","high",2),
 FamilyProfile(ResourceFamily.DOCUMENTARY_DATABASE,"high","low","medium","very_high","very_high","high",2),
 FamilyProfile(ResourceFamily.VIDEO,"medium","low","low","high","high","medium",4),
 FamilyProfile(ResourceFamily.PODCAST,"low","low","low","medium","medium","low",5),
 FamilyProfile(ResourceFamily.POSTER,"low","low","low","high","high","medium",4),
 FamilyProfile(ResourceFamily.PDF_DOCUMENT,"high","medium","medium","very_high","very_high","high",1),
)

IDENTIFIER_FAMILIES=("ED","TJ","A","AD","AR")
VERSIONING_OBSERVATION="latest-publications pages identify updates that cancel and replace previous editions"
SUPPORTED_DOCUMENT_TYPES=tuple(InrsDocumentType)
REFERENCE_DOCUMENT_TYPES={"ED":InrsDocumentType.ED,"TJ":InrsDocumentType.TJ,"AD":InrsDocumentType.AD,"AR":InrsDocumentType.AR}

def document_type_for_reference(reference:str)->InrsDocumentType:
 normalized=reference.strip().upper()
 for prefix,document_type in REFERENCE_DOCUMENT_TYPES.items():
  if normalized==prefix or normalized.startswith(prefix+" ") or normalized.startswith(prefix+"-"):return document_type
 return InrsDocumentType.AUTRE
