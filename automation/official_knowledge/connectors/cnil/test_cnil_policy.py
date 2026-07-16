import unittest
from automation.official_knowledge.connectors.cnil.cnil_models import ResourceCandidate
from automation.official_knowledge.connectors.cnil.cnil_policy import CnilSelectionPolicy,validate_candidate

def candidate(uri="https://www.cnil.fr/fr/travail-synthetic",typ="web_guidance",mime="text/html",themes=("employee_surveillance",)):
 return ResourceCandidate(uri,typ,"Synthetic",themes,("professional",),content_format=mime)

class CnilPolicyTests(unittest.TestCase):
 def test_cnil_and_linc_domains_allowed_with_approved_license(self):
  self.assertTrue(validate_candidate(candidate(),license_status="approved").accepted)
  self.assertTrue(validate_candidate(candidate("https://linc.cnil.fr/fr/synthetic"),license_status="approved").accepted)
 def test_external_domain_refused(self):self.assertFalse(validate_candidate(candidate("https://evil.example/fr/a"),license_status="approved").accepted)
 def test_professional_work_theme_allowed(self):self.assertTrue(validate_candidate(candidate(),license_status="approved").accepted)
 def test_transaction_and_form_refused(self):
  for uri in ("https://www.cnil.fr/fr/plainte","https://www.cnil.fr/fr/formulaire/test"):
   with self.subTest(uri=uri):self.assertEqual("TRANSACTIONAL_RESOURCE_REFUSED",validate_candidate(candidate(uri),license_status="approved").reason)
 def test_pending_restricted_prohibited_not_indexable(self):
  for status in ("pending","restricted","prohibited"):
   self.assertFalse(validate_candidate(candidate(),license_status=status).accepted)
 def test_mime_and_size(self):
  self.assertFalse(validate_candidate(candidate(mime="image/png"),license_status="approved").accepted)
  self.assertFalse(validate_candidate(candidate(),size_bytes=6_000_000,license_status="approved").accepted)
 def test_image_video_full_storage_refused(self):
  for typ in ("video_metadata","unknown"):
   self.assertFalse(validate_candidate(candidate(typ=typ),license_status="approved").accepted)
