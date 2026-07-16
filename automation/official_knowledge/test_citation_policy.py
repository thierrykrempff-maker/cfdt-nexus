import unittest
from datetime import datetime,timezone
from automation.official_knowledge.citation_policy import build_citation
from automation.official_knowledge.document_policy_models import CitationBasis,CitationSource

def source(identifier="s1",license_id="CC_BY",excerpt=None,internal=False):
 return CitationSource(identifier,"Titre synthétique",f"https://official.example/{identifier}",f"p-{identifier}",license_id,"official_guidance",datetime.now(timezone.utc),"v1",excerpt,internal)

class CitationPolicyTests(unittest.TestCase):
 def test_metadata_excerpt_internal_and_multiple(self):
  self.assertEqual(CitationBasis.METADATA_ONLY,build_citation(CitationBasis.METADATA_ONLY,(source(),)).basis)
  self.assertEqual("extrait",build_citation(CitationBasis.EXCERPT,(source(excerpt="extrait"),)).sources[0].excerpt)
  self.assertTrue(build_citation(CitationBasis.INTERNAL_DOCUMENT,(source(internal=True),)).sources[0].internal)
  self.assertEqual(2,len(build_citation(CitationBasis.MULTIPLE_SOURCES,(source(),source("s2"))).sources))
 def test_traceability_mandatory(self):
  bad=CitationSource("s","T","https://official.example","","CC_BY","official_guidance")
  with self.assertRaises(ValueError):build_citation(CitationBasis.METADATA_ONLY,(bad,))
 def test_excerpt_limit_and_forbidden(self):
  with self.assertRaises(ValueError):build_citation(CitationBasis.EXCERPT,(source(license_id="UNKNOWN",excerpt="x"),))
  with self.assertRaises(ValueError):build_citation(CitationBasis.EXCERPT,(source(license_id="CC_BY_ND",excerpt="x"*301),))
 def test_stable_identifier(self):
  moment=datetime(2026,1,1,tzinfo=timezone.utc);a=build_citation(CitationBasis.METADATA_ONLY,(source(),),moment);b=build_citation(CitationBasis.METADATA_ONLY,(source(),),moment);self.assertEqual(a.citation_id,b.citation_id)
