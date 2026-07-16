"""Fail-closed document and classification policies for future use."""
from __future__ import annotations
import unicodedata
from .dreets_catalog import DOMAIN_FAMILIES
from .dreets_models import ClassificationResult,DreetsDocumentType

KEYWORDS={
 "cse":("cse","comite social et economique","information consultation"),"temps_de_travail":("temps de travail","conges","repos"),
 "representation_du_personnel":("representant du personnel","salarie protege","mandat"),"inspection_du_travail":("inspection du travail","autorisation administrative"),
 "relations_collectives":("relations collectives","negociation collective"),"dialogue_social":("dialogue social",),"licenciement":("licenciement",),
 "rupture":("rupture",),"sante_au_travail":("sante au travail","medecin du travail"),"salaires":("salaire","smic"),
}

def _norm(text:str)->str:return "".join(c for c in unicodedata.normalize("NFKD",text.casefold()) if not unicodedata.combining(c))

def classify_document(title:str,category:str="fiche")->ClassificationResult:
 text=_norm(title);domains=tuple(domain for domain,terms in KEYWORDS.items() if any(term in text for term in terms))
 if not domains:domains=("questions_reponses_officielles",)
 if not set(domains)<=set(DOMAIN_FAMILIES):raise ValueError("unknown domain")
 return ClassificationResult(domains,category,"medium" if domains!=("questions_reponses_officielles",) else "low","metadata_only",True,("classification_does_not_establish_legal_applicability",))

def default_document_policy(category:str)->DreetsDocumentType:
 return DreetsDocumentType(category,"official_guidance","dreets_fail_closed_pending_review")
