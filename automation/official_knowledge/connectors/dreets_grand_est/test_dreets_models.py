import unittest
from automation.official_knowledge.connectors.dreets_grand_est.dreets_models import CONTENT_CATEGORIES,DreetsDocumentType,DreetsResourceCandidate

class ModelTests(unittest.TestCase):
 def test_all_content_categories(self): self.assertEqual({"guide","faq","actualité","instruction","circulaire","fiche","publication","dossier","communiqué","formulaire","modèle"},set(CONTENT_CATEGORIES))
 def test_unknown_license_is_metadata_only(self):
  policy=DreetsDocumentType("guide","official_guidance","pending");self.assertEqual("METADATA_ONLY",policy.index_level);self.assertFalse(policy.cache_allowed);self.assertFalse(policy.full_text_allowed);self.assertTrue(policy.require_provenance)
 def test_unknown_license_cannot_grant_cache(self): self.assertRaises(ValueError,DreetsDocumentType,"guide","official_guidance","pending","UNKNOWN","unknown","unknown","very_low","metadata_only",False,True)
 def test_candidate_rejects_wrong_source(self): self.assertRaises(ValueError,DreetsResourceCandidate,"other","","Synthetic","fiche",("cse",))
 def test_candidate_rejects_absolute_path(self): self.assertRaises(ValueError,DreetsResourceCandidate,"dreets_grand_est","C:\\secret.pdf","Synthetic","fiche",("cse",))
 def test_synthetic_candidate(self): self.assertEqual("pending_official_review",DreetsResourceCandidate("dreets_grand_est","","Synthetic","faq",("cse",)).access_review_status)
