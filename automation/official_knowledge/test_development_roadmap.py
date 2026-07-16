import unittest
from automation.official_knowledge.development_roadmap import WAVE_ORDER,recommended_sources
from automation.official_knowledge.source_catalog import CATALOG_BY_ID

class RoadmapTests(unittest.TestCase):
 def test_wave_zero_contains_existing_socles(self): self.assertTrue({"legifrance","judilibre","cnil","alsace_moselle_local_law"}<=set(WAVE_ORDER["WAVE_0"]))
 def test_wave_one_prepares_cssct_without_starting_it(self): self.assertTrue({"inrs","dreets_grand_est","dreal_grand_est","ineris","aida","aria"}<=set(WAVE_ORDER["WAVE_1"]))
 def test_recommendation_is_stable(self): self.assertEqual(recommended_sources(tuple(CATALOG_BY_ID.values())),recommended_sources(tuple(CATALOG_BY_ID.values())))
 def test_all_wave_members_exist(self): self.assertTrue(all(source_id in CATALOG_BY_ID for sources in WAVE_ORDER.values() for source_id in sources))
 def test_dreal_precedes_france_chimie(self):
  ordered=[source.source_id for source in recommended_sources(tuple(CATALOG_BY_ID.values()))];self.assertLess(ordered.index("dreal_grand_est"),ordered.index("france_chimie"))
