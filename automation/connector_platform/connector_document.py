from enum import StrEnum

class DocumentPolicy(StrEnum):
 METADATA_ONLY="METADATA_ONLY"; EXCERPTS="EXCERPTS"; FULLTEXT_ALLOWED="FULLTEXT_ALLOWED"; FORBIDDEN="FORBIDDEN"

def stores_text(policy:DocumentPolicy)->bool:return policy in {DocumentPolicy.EXCERPTS,DocumentPolicy.FULLTEXT_ALLOWED}
