import socket,unittest
from unittest.mock import patch
from automation.official_knowledge import NETWORK_DISABLED
from automation.official_knowledge.connectors.cnil import CNIL_NETWORK_NOT_IMPLEMENTED
from automation.official_knowledge.connectors.cnil.cnil_connector import CnilConnector
from automation.official_knowledge.connectors.cnil.cnil_models import RawOfficialResource,ResourceCandidate
from automation.official_knowledge.connectors.cnil.cnil_parser import parse_synthetic_resource
from automation.official_knowledge.connectors.cnil.cnil_sync import synchronize

class CnilContractTests(unittest.TestCase):
 def test_all_transport_contract_methods_blocked(self):
  connector=CnilConnector();candidate=ResourceCandidate("https://www.cnil.fr/fr/synthetic","web_guidance","Synthetic")
  for call in (lambda:connector.discover_resources("work"),lambda:connector.fetch_resource(candidate),lambda:connector.validate_resource(RawOfficialResource(candidate,b"synthetic","text/html")),lambda:connector.parse_resource(RawOfficialResource(candidate,b"synthetic","text/html")),lambda:synchronize()):
   with self.assertRaisesRegex(RuntimeError,CNIL_NETWORK_NOT_IMPLEMENTED):call()
 def test_network_default_unchanged_and_no_real_request(self):
  self.assertEqual("NETWORK_DISABLED_BY_DEFAULT",NETWORK_DISABLED)
  with patch.object(socket,"create_connection",side_effect=AssertionError("network called")):
   with self.assertRaises(RuntimeError):CnilConnector().discover_resources("synthetic")
 def test_synthetic_approved_parse(self):
  candidate=ResourceCandidate("https://www.cnil.fr/fr/synthetic","news","Actualité synthétique",("cybersecurity_breaches",),content_format="text/html")
  parsed=parse_synthetic_resource(RawOfficialResource(candidate,b"Contenu entierement synthetique.","text/html"),license_id="synthetic-approved",license_status="approved")
  self.assertTrue(parsed.resource.indexable);self.assertEqual("public_official",parsed.resource.provenance["confidentiality_level"])
 def test_synthetic_pending_non_indexable_and_by_nd_traced(self):
  candidate=ResourceCandidate("https://www.cnil.fr/fr/synthetic-guide","guide","Guide synthétique",content_format="application/pdf")
  parsed=parse_synthetic_resource(RawOfficialResource(candidate,b"%PDF synthetic","application/pdf"),license_id="CC-BY-ND-4.0-FR",license_status="pending")
  self.assertFalse(parsed.resource.indexable);self.assertEqual("CC-BY-ND-4.0-FR",parsed.resource.license_id);self.assertEqual("LICENSE_NOT_APPROVED",parsed.resource.rejection_reason)
