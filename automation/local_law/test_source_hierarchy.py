import unittest
from automation.official_knowledge.source_registry import get_source
from .source_hierarchy import SOURCES,source_for

class SourceTests(unittest.TestCase):
 def test_registry_sources_disabled_and_architecture_only(self):
  for source in SOURCES:
   registered=get_source(source.source_id);self.assertFalse(registered.enabled);self.assertEqual("architecture_only",registered.connector_status)
 def test_law_is_primary(self): self.assertEqual("primary_law",source_for("alsace_moselle_local_law").authority_level)
 def test_case_law_is_distinct(self): self.assertEqual("official_case_law",source_for("alsace_moselle_case_law").authority_level)
 def test_dreets_is_not_law(self): self.assertFalse(source_for("dreets_grand_est_local_law").normative);self.assertEqual("official_guidance",source_for("dreets_grand_est_local_law").authority_level)
 def test_service_public_is_not_primary(self): self.assertEqual("official_practical_information",source_for("service_public_local_law").authority_level)
 def test_only_four_approved_source_roles(self): self.assertEqual(4,len(SOURCES))
