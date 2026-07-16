import unittest
from datetime import timedelta
from automation.official_knowledge.document_cache_policy import CachePolicy
from automation.official_knowledge.document_policy import DocumentPolicy,evaluate_document
from automation.official_knowledge.document_policy_models import CacheMode,IndexLevel
from automation.official_knowledge.index_policy import connector_level,decide_index
from automation.official_knowledge.license_policy import license_capabilities

class DocumentPolicyTests(unittest.TestCase):
 def test_all_index_levels(self):
  for value in ("NONE","METADATA_ONLY","EXCERPTS","FULLTEXT_ALLOWED","INTERNE_ONLY"):self.assertEqual(value,connector_level(value).value)
 def test_metadata_index_for_unknown_license(self):
  self.assertTrue(decide_index(IndexLevel.METADATA_ONLY,license_capabilities("UNKNOWN")).allowed)
 def test_fulltext_refused_for_nd(self):
  self.assertFalse(decide_index(IndexLevel.FULLTEXT_ALLOWED,license_capabilities("CC_BY_ND")).allowed)
 def test_internal_only(self):
  p=license_capabilities("UNKNOWN");self.assertTrue(decide_index(IndexLevel.INTERNE_ONLY,p,internal=True).allowed);self.assertFalse(decide_index(IndexLevel.INTERNE_ONLY,p,internal=False).allowed)
 def test_missing_provenance_blocks_cache_and_index(self):
  policy=DocumentPolicy("CC_BY",IndexLevel.FULLTEXT_ALLOWED,CachePolicy(CacheMode.TEMPORARY,timedelta(days=1)),"official_guidance")
  result=evaluate_document(policy,has_provenance=False);self.assertFalse(result["index"].allowed);self.assertFalse(result["cache"].allowed)
 def test_composed_open_policy(self):
  policy=DocumentPolicy("LICENCE_OUVERTE",IndexLevel.FULLTEXT_ALLOWED,CachePolicy(CacheMode.PERMANENT,None),"institutional_information")
  result=evaluate_document(policy,has_provenance=True);self.assertTrue(all(x.allowed for x in result.values()))
