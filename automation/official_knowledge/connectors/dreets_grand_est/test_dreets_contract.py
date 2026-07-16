import unittest
from automation.official_knowledge import NETWORK_DISABLED
from automation.official_knowledge.connectors.dreets_grand_est import DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED
from automation.official_knowledge.connectors.dreets_grand_est.dreets_connector import DreetsGrandEstConnector
from automation.official_knowledge.connectors.dreets_grand_est.dreets_sync import synchronize
from automation.official_knowledge.source_registry import get_source

class ContractTests(unittest.TestCase):
 def test_global_network_disabled(self): self.assertEqual("NETWORK_DISABLED_BY_DEFAULT",NETWORK_DISABLED)
 def test_registry_disabled_architecture_only(self):
  source=get_source("dreets_grand_est");self.assertFalse(source.enabled);self.assertEqual("architecture_only",source.connector_status)
 def test_connector_class_disabled(self):
  connector=DreetsGrandEstConnector();self.assertFalse(connector.enabled);self.assertEqual("architecture_only",connector.connector_status)
 def test_discovery_blocked(self):
  with self.assertRaisesRegex(RuntimeError,DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED):DreetsGrandEstConnector().discover_resources("synthetic")
 def test_fetch_blocked(self):
  with self.assertRaisesRegex(RuntimeError,DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED):DreetsGrandEstConnector().fetch_resource(None)
 def test_classification_operation_blocked(self):
  with self.assertRaisesRegex(RuntimeError,DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED):DreetsGrandEstConnector().classify_resource(None)
 def test_sync_blocked(self):
  with self.assertRaisesRegex(RuntimeError,DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED):synchronize()
