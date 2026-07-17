import unittest

from automation.connector_platform import NETWORK_DISABLED_BY_DEFAULT
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_health import HealthStatus
from automation.connector_platform.connector_license import LicenseId

from .anact_catalog import CONFIRMED_ENTRY_POINTS,FAMILY_BY_ID
from .anact_contract import AnactConnector
from .anact_freshness import FRESHNESS_BY_FAMILY,ResourceLifecycle
from .anact_legal_policy import ANACT_LEGAL_POLICY,LegalStatus
from .anact_source_audit import AUDIT_BY_MECHANISM,AUDIT_RECORDS,AuditDecision,EvidenceLevel,SourceAuditRecord
from .anact_source_registry import REGION_BY_ID,REGIONAL_ENTITIES,RegionalEvidence

class AnactSourceAuditTests(unittest.TestCase):
 def test_audit_records_unique(self):self.assertEqual(len(AUDIT_RECORDS),len(AUDIT_BY_MECHANISM))
 def test_confirmed_records_have_responses(self):self.assertTrue(all(record.url and record.http_status for record in AUDIT_RECORDS if record.evidence is EvidenceLevel.CONFIRMED))
 def test_official_domains_only(self):self.assertTrue(all(record.url is None or record.url.startswith("https://www.anact.fr") for record in AUDIT_RECORDS))
 def test_non_official_domain_rejected(self):
  with self.assertRaises(ValueError):SourceAuditRecord("invalid","https://example.invalid",EvidenceLevel.CONFIRMED,AuditDecision.RETAINED,"2026-07-17",200,"text/html")
 def test_observed_mime_types(self):self.assertEqual("text/plain",AUDIT_BY_MECHANISM["robots_txt"].mime_type);self.assertTrue(AUDIT_BY_MECHANISM["xml_sitemap"].mime_type.startswith("text/xml"))
 def test_sitemap_retained(self):self.assertIs(AuditDecision.RETAINED,AUDIT_BY_MECHANISM["xml_sitemap"].decision);self.assertTrue(AUDIT_BY_MECHANISM["xml_sitemap"].stable_identifiers)
 def test_search_rejected(self):self.assertIs(AuditDecision.REJECTED,AUDIT_BY_MECHANISM["internal_search"].decision)
 def test_faceted_pagination_rejected(self):self.assertIs(EvidenceLevel.REJECTED,AUDIT_BY_MECHANISM["faceted_pagination"].evidence)
 def test_api_not_confirmed(self):self.assertIs(EvidenceLevel.NOT_CONFIRMED,AUDIT_BY_MECHANISM["public_api"].evidence)
 def test_feed_not_confirmed(self):self.assertIs(EvidenceLevel.NOT_CONFIRMED,AUDIT_BY_MECHANISM["rss_atom"].evidence)
 def test_structured_metadata_not_confirmed(self):self.assertIs(AuditDecision.DEFERRED,AUDIT_BY_MECHANISM["structured_metadata"].decision)
 def test_downloads_not_confirmed(self):self.assertIs(EvidenceLevel.NOT_CONFIRMED,AUDIT_BY_MECHANISM["downloadable_documents"].evidence)
 def test_entry_points_match_confirmed_audit(self):self.assertEqual("https://www.anact.fr/sitemap.xml",CONFIRMED_ENTRY_POINTS["sitemap"]);self.assertIn("themes",CONFIRMED_ENTRY_POINTS)
 def test_families_have_freshness_policy(self):self.assertEqual(set(FAMILY_BY_ID),set(FRESHNESS_BY_FAMILY))
 def test_freshness_positive(self):self.assertTrue(all(policy.revalidate_after_days>0 for policy in FRESHNESS_BY_FAMILY.values()))
 def test_freshness_is_declarative(self):self.assertTrue(all(policy.method in {"sitemap_metadata","conditional_metadata","manual_review"} for policy in FRESHNESS_BY_FAMILY.values()))
 def test_lifecycle_complete(self):self.assertEqual({"active","moved","removed","archived","unknown"},{item.value for item in ResourceLifecycle})
 def test_legal_policy_conservative(self):self.assertIs(LicenseId.DOCUMENT_SPECIFIC,ANACT_LEGAL_POLICY.license_id);self.assertIs(DocumentPolicy.METADATA_ONLY,ANACT_LEGAL_POLICY.document_policy);self.assertIs(LegalStatus.HUMAN_REVIEW,ANACT_LEGAL_POLICY.reuse_status)
 def test_no_cache_fulltext_or_excerpt(self):self.assertFalse(ANACT_LEGAL_POLICY.cache_allowed);self.assertFalse(ANACT_LEGAL_POLICY.fulltext_allowed);self.assertFalse(ANACT_LEGAL_POLICY.excerpts_allowed)
 def test_regional_entities_unique(self):self.assertEqual(len(REGIONAL_ENTITIES),len(REGION_BY_ID))
 def test_regional_entities_centralized(self):self.assertTrue(all(entity.centralized_on_anact and entity.official_url.startswith("https://www.anact.fr/") for entity in REGIONAL_ENTITIES))
 def test_grand_est_http_confirmed(self):self.assertIs(RegionalEvidence.HTTP_CONFIRMED,REGION_BY_ID["grand_est"].evidence)
 def test_other_regions_only_sitemap_observed(self):self.assertTrue(all(entity.evidence is RegionalEvidence.SITEMAP_OBSERVED for entity in REGIONAL_ENTITIES if entity.region_id!="grand_est"))
 def test_connector_exposes_audit(self):self.assertEqual(AUDIT_RECORDS,AnactConnector().source_audit());self.assertIs(ANACT_LEGAL_POLICY,AnactConnector().legal_policy())
 def test_connector_stays_disabled(self):self.assertFalse(AnactConnector.enabled);self.assertEqual("architecture_only",AnactConnector.connector_status);self.assertIs(HealthStatus.DISABLED,AnactConnector.health.status);self.assertEqual("NETWORK_DISABLED_BY_DEFAULT",NETWORK_DISABLED_BY_DEFAULT)
 def test_deterministic_audit(self):self.assertEqual(AUDIT_RECORDS,AUDIT_RECORDS);self.assertEqual(tuple(FRESHNESS_BY_FAMILY),tuple(FRESHNESS_BY_FAMILY))

if __name__=="__main__":unittest.main()
