import json
import unittest

from .dreets_access_review import (
    ARCHITECTURE_COMPARISON,
    CONSULTED_DOMAINS,
    DOCUMENT_POLICY,
    EVIDENCE,
    NETWORK_DISABLED_BY_DEFAULT,
    RECOMMENDATION,
    SAMPLE,
    build_review,
)


class DreetsAccessReviewTests(unittest.TestCase):
    def test_only_authorized_administrative_domains_were_recorded(self):
        self.assertEqual(CONSULTED_DOMAINS, ("grand-est.dreets.gouv.fr", "dreets.gouv.fr"))

    def test_rss_is_not_reported_as_validated(self):
        rss = next(item for item in EVIDENCE if item.subject == "rss")
        self.assertEqual(rss.status, "published_link_payload_unverified")

    def test_api_absence_is_not_overclaimed(self):
        api = next(item for item in EVIDENCE if item.subject == "public_api")
        self.assertEqual(api.status, "not_identified_in_limited_review")

    def test_site_plan_is_not_xml_sitemap(self):
        plan = next(item for item in EVIDENCE if item.subject == "html_site_plan")
        self.assertIn("not an XML sitemap", plan.note)

    def test_policy_remains_metadata_only(self):
        self.assertEqual(DOCUMENT_POLICY["index_level"], "METADATA_ONLY")
        self.assertFalse(DOCUMENT_POLICY["cache_allowed"])
        self.assertFalse(DOCUMENT_POLICY["full_text_allowed"])
        self.assertFalse(DOCUMENT_POLICY["extracts_retained"])

    def test_citation_and_provenance_are_mandatory(self):
        self.assertTrue(DOCUMENT_POLICY["citation_required"])
        self.assertTrue(DOCUMENT_POLICY["provenance_required"])

    def test_targeted_pages_are_current_recommendation(self):
        self.assertEqual(RECOMMENDATION["primary"], "targeted_pages_metadata_only")

    def test_rss_requires_future_validation(self):
        self.assertEqual(RECOMMENDATION["candidate_after_validation"], "rss_metadata_discovery")

    def test_no_transport_or_synchronization(self):
        self.assertTrue(NETWORK_DISABLED_BY_DEFAULT)
        self.assertFalse(RECOMMENDATION["network_transport_implemented"])
        self.assertFalse(RECOMMENDATION["synchronization_enabled"])

    def test_all_architectures_are_compared(self):
        self.assertEqual({item["mode"] for item in ARCHITECTURE_COMPARISON}, {"api", "rss", "sitemap", "targeted_pages", "manual_ingestion"})

    def test_sample_is_metadata_only(self):
        allowed = {"url", "title", "date", "family", "document_type"}
        self.assertTrue(SAMPLE)
        self.assertTrue(all(set(item.to_dict()) == allowed for item in SAMPLE))

    def test_sample_stays_on_official_domain(self):
        self.assertTrue(all(item.url.startswith("https://grand-est.dreets.gouv.fr/") for item in SAMPLE))

    def test_sample_covers_requested_families(self):
        families = {item.family for item in SAMPLE}
        self.assertTrue({"cse", "inspection_du_travail", "sante_au_travail"} <= families)
        self.assertTrue(any("moselle" in family for family in families))

    def test_review_is_json_serializable(self):
        json.dumps(build_review(), ensure_ascii=False)

    def test_review_contains_no_document_content(self):
        review = build_review()
        self.assertNotIn("content", review)
        self.assertNotIn("full_text", review)


if __name__ == "__main__":
    unittest.main()
