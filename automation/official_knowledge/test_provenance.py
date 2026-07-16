import unittest
from automation.official_knowledge.authority import validate_authority
from automation.official_knowledge.fingerprints import content_sha256,content_unchanged,is_new_version,uri_fingerprint,version_id
from automation.official_knowledge.licensing import LicensePolicy
from automation.official_knowledge.provenance_models import ProvenanceRecord

class ProvenanceTests(unittest.TestCase):
 def test_public_provenance_and_authority(self):
  p=ProvenanceRecord("p1","synthetic","unknown","https://official.example/a","https://official.example/a","Synthetic Publisher")
  self.assertEqual("public_official",p.confidentiality_level);self.assertEqual("official_guidance",validate_authority("official_guidance"))
 def test_absolute_local_path_refused(self):
  with self.assertRaises(ValueError):ProvenanceRecord("p","s","unknown","C:/secret","https://official.example","P")
 def test_license_restrictive_by_default(self):
  p=LicensePolicy("pending");self.assertFalse(p.redistribution_allowed);self.assertFalse(p.caching_allowed);self.assertFalse(p.full_text_storage_allowed)
 def test_stable_fingerprints_and_versions(self):
  h=content_sha256("synthetic");self.assertEqual(h,content_sha256("synthetic"));self.assertTrue(content_unchanged(h,"synthetic"));self.assertTrue(is_new_version(h,"changed"))
  self.assertEqual(uri_fingerprint("https://OFFICIAL.example/a"),uri_fingerprint("https://official.example/a"));self.assertEqual(version_id("s","https://official.example",h),version_id("s","https://official.example",h))
