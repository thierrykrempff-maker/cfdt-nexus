import unittest
from automation.official_knowledge.source_catalog import CATALOG,CATALOG_BY_ID,get_catalog_source

class CatalogTests(unittest.TestCase):
 def test_ids_unique(self): self.assertEqual(len(CATALOG),len(CATALOG_BY_ID))
 def test_required_sources_present(self):
  required={"legifrance","judilibre","code_travail_numerique","dreets_grand_est","dreal_grand_est","inrs","ineris","aida","aria","georisques","anact","ameli","urssaf","echa","gestis","france_chimie","observatoire_chimie","opco_2i","data_gouv_fr"};self.assertTrue(required<=set(CATALOG_BY_ID))
 def test_all_disabled(self): self.assertTrue(all(not source.enabled for source in CATALOG))
 def test_no_unproved_implemented_connector(self): self.assertTrue(all(source.connector_status!="implemented" for source in CATALOG))
 def test_france_chimie_position(self):
  source=get_catalog_source("france_chimie");self.assertEqual("employer_federation",source.publisher_type);self.assertEqual("employer_side_institution",source.institutional_position);self.assertEqual("institutional_information",source.authority_level);self.assertIn("not_neutral",source.caveats)
 def test_dreets_guidance_not_law(self): self.assertEqual("official_guidance",get_catalog_source("dreets_grand_est").authority_level)
 def test_dreal_is_high_for_seveso_context(self):
  source=get_catalog_source("dreal_grand_est");self.assertEqual("very_high",source.relevance_for_ineos_sarralbe);self.assertEqual("WAVE_1",source.development_wave)
 def test_gestis_is_foreign_complement(self):
  source=get_catalog_source("gestis");self.assertEqual("foreign_public_institution",source.publisher_type);self.assertIn("echa",source.dependency_sources)
 def test_local_law_and_health_regime_are_distinct(self): self.assertNotEqual(get_catalog_source("alsace_moselle_local_law").source_id,get_catalog_source("alsace_moselle_health_regime").source_id)
 def test_priority_does_not_equal_authority(self):
  dreal=get_catalog_source("dreal_grand_est");self.assertEqual("PRIORITY_2",dreal.nexus_priority_level);self.assertNotEqual("primary_law",dreal.authority_level)
 def test_catalog_has_no_absolute_path(self): self.assertFalse(any(":\\" in str(source.to_dict()) for source in CATALOG))
