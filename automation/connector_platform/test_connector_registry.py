import unittest
from .connector_contract import ConnectorContract
from .connector_metadata import ConnectorMetadata
from .connector_registry import ConnectorRegistry

def contract(identifier):return ConnectorContract(ConnectorMetadata(identifier,identifier.title(),"Synthetic publisher"))

class RegistryTests(unittest.TestCase):
 def test_registry_starts_empty(self):self.assertEqual((),ConnectorRegistry().list_ids())
 def test_register_and_get(self):
  registry=ConnectorRegistry();value=contract("alpha");registry.register(value);self.assertIs(value,registry.get("alpha"))
 def test_ids_are_sorted(self):
  registry=ConnectorRegistry();registry.register(contract("zeta"));registry.register(contract("alpha"));self.assertEqual(("alpha","zeta"),registry.list_ids())
 def test_duplicate_refused(self):
  registry=ConnectorRegistry();registry.register(contract("alpha"))
  with self.assertRaises(ValueError):registry.register(contract("alpha"))
 def test_unknown_raises_key_error(self):
  with self.assertRaises(KeyError):ConnectorRegistry().get("missing")
