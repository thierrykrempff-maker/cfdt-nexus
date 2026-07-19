from dataclasses import dataclass
from typing import Protocol
from automation.official_knowledge.document_registry import DocumentChange,DocumentRecord
from .inrs_models import InrsDocumentIdentity

@dataclass(frozen=True)
class InrsDocumentContract:
 policy:str="METADATA_ONLY";cache_allowed:bool=False;text_indexing_allowed:bool=False
 local_copy_allowed:bool=False;pdf_storage_allowed:bool=False;html_storage_allowed:bool=False
 full_text_allowed:bool=False;download_allowed:bool=False;provenance_required:bool=True
 citation_required:bool=True;https_required:bool=True
 def __post_init__(self):
  if self.policy!="METADATA_ONLY":raise ValueError("INRS LOT 0 requires METADATA_ONLY")
  forbidden=(self.cache_allowed,self.text_indexing_allowed,self.local_copy_allowed,self.pdf_storage_allowed,self.html_storage_allowed,self.full_text_allowed,self.download_allowed)
  if any(forbidden):raise ValueError("INRS LOT 0 forbids document content")
  if not all((self.provenance_required,self.citation_required,self.https_required)):raise ValueError("provenance, citation and HTTPS are mandatory")

class InrsDocumentRegistryPort(Protocol):
 def register_document(self,document:DocumentRecord)->DocumentChange:...
 def update_document(self,document:DocumentRecord)->DocumentChange:...
 def find_document(self,document_id:str)->DocumentRecord|None:...

class InrsConnectorContract(Protocol):
 def discover(self,scope:str)->list[InrsDocumentIdentity]:...
 def fetch(self,identity:InrsDocumentIdentity)->bytes:...
 def synchronize(self)->None:...

INRS_DOCUMENT_CONTRACT=InrsDocumentContract()

# Historical public import path remains supported without a circular import.
def __getattr__(name:str):
 if name=="InrsConnector":
  from .inrs_connector import InrsConnector
  return InrsConnector
 raise AttributeError(name)
