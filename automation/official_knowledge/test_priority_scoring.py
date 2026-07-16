import unittest
from automation.official_knowledge.priority_scoring import ScoreFactors,development_score
from automation.official_knowledge.source_catalog import DEVELOPMENT_SCORES

class ScoringTests(unittest.TestCase):
 def test_deterministic(self):
  factors=ScoreFactors(25,15,15,20,10,5,5,5);self.assertEqual(100,development_score(factors));self.assertEqual(development_score(factors),development_score(factors))
 def test_bounded(self): self.assertTrue(all(0<=score<=100 for score in DEVELOPMENT_SCORES.values()))
 def test_rejects_out_of_range(self): self.assertRaises(ValueError,ScoreFactors,26,0,0,0,0,0,0,0)
 def test_dreal_can_score_above_institutional_source(self): self.assertGreater(DEVELOPMENT_SCORES["dreal_grand_est"],DEVELOPMENT_SCORES["france_chimie"])
 def test_authority_and_score_are_separate(self): self.assertGreater(DEVELOPMENT_SCORES["dreal_grand_est"],0)
