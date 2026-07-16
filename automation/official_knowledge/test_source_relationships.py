import unittest
from automation.official_knowledge.source_catalog import CATALOG_BY_ID
from automation.official_knowledge.source_relationships import RELATIONSHIPS,validate_relationships

class RelationshipTests(unittest.TestCase):
 def test_relationships_valid_and_acyclic(self): validate_relationships(set(CATALOG_BY_ID))
 def test_dreets_regional_relationship(self): self.assertIn(("dreets_grand_est","regional_instance_of","dreets_national"),{(r.subject_id,r.relation_type,r.object_id) for r in RELATIONSHIPS})
 def test_france_chimie_is_employer_position(self): self.assertTrue(any(r.subject_id=="france_chimie" and r.relation_type=="employer_position_on" for r in RELATIONSHIPS))
 def test_service_public_does_not_supersede_law(self): self.assertFalse(any(r.subject_id=="service_public" and r.relation_type=="supersedes" for r in RELATIONSHIPS))
 def test_aida_and_aria_are_technical(self): self.assertTrue(all(any(r.subject_id==source_id and r.relation_type=="technical_reference_for" for r in RELATIONSHIPS) for source_id in ("aida","aria")))
