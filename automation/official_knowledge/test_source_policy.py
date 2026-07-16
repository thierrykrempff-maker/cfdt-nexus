import unittest
from automation.official_knowledge.source_policy import AccessPolicy,validate_payload,validate_redirect,validate_url

class PolicyTests(unittest.TestCase):
 def setUp(self):self.policy=AccessPolicy(("official.example",))
 def test_allowed_domain_and_subdomain(self):
  self.assertEqual("https://official.example/a",validate_url("https://official.example/a",self.policy));validate_url("https://sub.official.example/a",self.policy)
 def test_external_and_redirect_refused(self):
  with self.assertRaisesRegex(ValueError,"DOMAIN_REFUSED"):validate_url("https://evil.example",self.policy)
  with self.assertRaisesRegex(ValueError,"DOMAIN_REFUSED"):validate_redirect("https://official.example","https://evil.example",self.policy)
 def test_http_file_localhost_private_and_credentials_refused(self):
  for url in ("http://official.example","file:///tmp/a","https://localhost/a","https://127.0.0.1/a","https://user:pass@official.example/a"):
   with self.subTest(url=url),self.assertRaises(ValueError):validate_url(url,self.policy)
 def test_payload_limits(self):
  validate_payload(10,"application/json",self.policy)
  with self.assertRaises(ValueError):validate_payload(20_000_000,"application/json",self.policy)
  with self.assertRaises(ValueError):validate_payload(10,"application/x-unknown",self.policy)
