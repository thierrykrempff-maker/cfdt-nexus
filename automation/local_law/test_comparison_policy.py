import unittest
from .comparison_policy import ComparisonRequest,compare

class ComparisonTests(unittest.TestCase):
 def test_no_absolute_local_priority(self):
  result=compare(ComparisonRequest(True,True,True,True));self.assertIsNone(result.selected_rule);self.assertTrue(result.legal_review_required)
 def test_ineos_and_collective_rules_are_not_overwritten(self): self.assertIn("objects_may_differ",compare(ComparisonRequest(True,False,True,True,False)).unresolved_conflicts)
 def test_public_policy_and_derogation_checks_required(self):
  result=compare(ComparisonRequest(True,False,False,False));self.assertIn("public_policy_not_checked",result.unresolved_conflicts);self.assertIn("derogation_not_checked",result.unresolved_conflicts)
 def test_single_scoped_rule_can_be_selected_only_after_checks(self): self.assertEqual("local",compare(ComparisonRequest(True,False,False,False,True,True,True)).selected_rule)
 def test_missing_text_keeps_review(self): self.assertTrue(compare(ComparisonRequest(None,True,None,None,True,True,True)).legal_review_required)
