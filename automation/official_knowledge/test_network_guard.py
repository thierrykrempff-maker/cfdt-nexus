import socket,unittest
from unittest.mock import patch
from automation.official_knowledge import NETWORK_DISABLED
from automation.official_knowledge.kill_switch import network_enabled,source_enabled
from automation.official_knowledge.network_guard import NetworkGuard,RequestSpec
from automation.official_knowledge.source_policy import AccessPolicy

class NetworkGuardTests(unittest.TestCase):
 def test_network_disabled_by_default_and_invalid(self):
  self.assertFalse(network_enabled({}));self.assertFalse(network_enabled({"OFFICIAL_KNOWLEDGE_NETWORK_ENABLED":"maybe"}))
 def test_global_and_source_switch(self):
  env={"OFFICIAL_KNOWLEDGE_NETWORK_ENABLED":"true","OFFICIAL_KNOWLEDGE_SOURCE_SYNTHETIC_ENABLED":"1"};self.assertTrue(source_enabled("synthetic",env));self.assertFalse(source_enabled("other",env))
 def test_guard_always_blocks_even_when_flags_enabled(self):
  env={"OFFICIAL_KNOWLEDGE_NETWORK_ENABLED":"true","OFFICIAL_KNOWLEDGE_SOURCE_SYNTHETIC_ENABLED":"true"}
  with self.assertRaisesRegex(RuntimeError,NETWORK_DISABLED):NetworkGuard().authorize(RequestSpec("synthetic","https://official.example/a"),AccessPolicy(("official.example",)),env)
 def test_execute_cannot_contact_network(self):
  with patch.object(socket,"create_connection",side_effect=AssertionError("network called")):
   with self.assertRaisesRegex(RuntimeError,NETWORK_DISABLED):NetworkGuard().execute()
 def test_internal_corpus_domains_separated(self):
  p=AccessPolicy(("official.example",))
  for url in ("https://ccsememoryengine/a","https://protection_sociale_engine/a"):
   with self.assertRaises(ValueError):NetworkGuard().authorize(RequestSpec("synthetic",url),p,{})
