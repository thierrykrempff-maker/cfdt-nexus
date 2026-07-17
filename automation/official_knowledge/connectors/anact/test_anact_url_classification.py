import inspect
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_license import LicenseId

from .anact_classification_models import (
    ClassificationDecision,
    ClassificationRule,
    HumanValidationStatus,
    UrlCategory,
)
from .anact_classification_rules import CLASSIFICATION_RULES, RULESET_VERSION
from .anact_contract import AnactConnector
from .anact_models import ConfidenceLevel
from .anact_review_queue import AnactReviewQueue
from .anact_transport_models import FilterDecision, SitemapCandidate
from .anact_url_classifier import AnactUrlClassifier


NOW = datetime(2026, 7, 17, tzinfo=timezone.utc)


def candidate(url: str, *, synthetic_only: bool = True) -> SitemapCandidate:
    path = "/" + url.split("/", 3)[-1] if url.count("/") >= 3 else "/"
    return SitemapCandidate(
        url,
        url,
        "www.anact.fr",
        path,
        "url",
        None,
        None,
        None,
        None,
        "national",
        None,
        NOW,
        NOW,
        "https://www.anact.fr/sitemap.xml",
        None,
        None,
        "valid",
        FilterDecision.ACCEPTED,
        None,
        "source-fingerprint",
        synthetic_only,
    )


class AnactUrlClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.classifier = AnactUrlClassifier()

    def assert_category(self, url: str, category: UrlCategory) -> None:
        result = self.classifier.classify_url(url)
        self.assertIs(category, result.category)
        self.assertIs(ClassificationDecision.AUTO_ACCEPTED, result.decision)

    def test_thematic_page(self): self.assert_category("https://www.anact.fr/themes/qvct", UrlCategory.THEMATIC_PAGE)
    def test_publication(self): self.assert_category("https://www.anact.fr/publications/reference", UrlCategory.PUBLICATION)
    def test_guide(self): self.assert_category("https://www.anact.fr/guides/reference", UrlCategory.GUIDE)
    def test_tool(self): self.assert_category("https://www.anact.fr/outils/reference", UrlCategory.TOOL)
    def test_study(self): self.assert_category("https://www.anact.fr/etudes/reference", UrlCategory.STUDY)
    def test_dossier(self): self.assert_category("https://www.anact.fr/dossiers/reference", UrlCategory.DOSSIER)
    def test_practical_sheet(self): self.assert_category("https://www.anact.fr/fiches-pratiques/reference", UrlCategory.PRACTICAL_SHEET)
    def test_news(self): self.assert_category("https://www.anact.fr/actualites/reference", UrlCategory.NEWS)
    def test_event(self): self.assert_category("https://www.anact.fr/evenements/reference", UrlCategory.EVENT)
    def test_legal_page(self): self.assert_category("https://www.anact.fr/mentions-legales", UrlCategory.LEGAL_PAGE)
    def test_institutional_page(self): self.assert_category("https://www.anact.fr/qui-sommes-nous", UrlCategory.INSTITUTIONAL_PAGE)

    def test_regional_root(self):
        result = self.classifier.classify_url("https://www.anact.fr/grand-est")
        self.assertEqual((UrlCategory.REGIONAL_ARACT_PAGE, "grand_est"), (result.category, result.region_id))

    def test_regional_child(self):
        result = self.classifier.classify_url("https://www.anact.fr/grand-est/actualite-locale")
        self.assertEqual((UrlCategory.REGIONAL_ARACT_PAGE, "grand_est"), (result.category, result.region_id))

    def test_ambiguous_slug_requires_review(self):
        result = self.classifier.classify_url("https://www.anact.fr/ressource/guide-qvct")
        self.assertEqual((UrlCategory.GUIDE, ClassificationDecision.HUMAN_REVIEW_REQUIRED, ConfidenceLevel.MEDIUM), (result.category, result.decision, result.confidence))

    def test_unknown_url_is_unclassified(self):
        result = self.classifier.classify_url("https://www.anact.fr/contenu-sans-regle")
        self.assertEqual((UrlCategory.UNKNOWN_RESOURCE, ClassificationDecision.UNCLASSIFIED), (result.category, result.decision))

    def test_external_url_is_rejected(self):
        result = self.classifier.classify_url("https://example.invalid/publications/x")
        self.assertEqual((ClassificationDecision.REJECTED, "domain_not_allowed"), (result.decision, result.rejection_reason))

    def test_robots_route_is_rejected(self):
        result = self.classifier.classify_url("https://www.anact.fr/search/qvct")
        self.assertEqual((ClassificationDecision.REJECTED, "robots_forbidden_path"), (result.decision, result.rejection_reason))

    def test_faceted_route_is_rejected(self):
        result = self.classifier.classify_url("https://www.anact.fr/actualites?page=2")
        self.assertEqual(ClassificationDecision.REJECTED, result.decision)

    def test_specific_rule_precedes_generic_slug(self):
        result = self.classifier.classify_url("https://www.anact.fr/actualites/guide-du-mois")
        self.assertEqual((UrlCategory.NEWS, "news_path"), (result.category, result.rule_id))

    def test_same_priority_conflict_requires_review(self):
        rules = (
            ClassificationRule("a", "v1", 1, UrlCategory.GUIDE, ConfidenceLevel.HIGH, "a", path_prefixes=("/x",)),
            ClassificationRule("b", "v1", 1, UrlCategory.TOOL, ConfidenceLevel.HIGH, "b", path_prefixes=("/x",)),
        )
        result = AnactUrlClassifier(rules).classify_url("https://www.anact.fr/x/item")
        self.assertEqual((UrlCategory.UNKNOWN_RESOURCE, ClassificationDecision.HUMAN_REVIEW_REQUIRED), (result.category, result.decision))

    def test_rule_order_is_explicit(self):
        priorities = tuple(rule.priority for rule in AnactUrlClassifier().rules)
        self.assertEqual(tuple(sorted(priorities)), priorities)

    def test_rules_are_versioned(self): self.assertTrue(all(rule.version == RULESET_VERSION for rule in CLASSIFICATION_RULES))

    def test_deterministic_output(self):
        first = self.classifier.classify_url("https://www.anact.fr/themes/qvct")
        second = self.classifier.classify_url("https://www.anact.fr/themes/qvct")
        self.assertEqual(first, second)

    def test_stable_fingerprint(self):
        first = self.classifier.classify_url("https://www.anact.fr/publications/x").fingerprint
        second = AnactUrlClassifier().classify_url("https://www.anact.fr/publications/x").fingerprint
        self.assertEqual(first, second)

    def test_candidate_metadata_is_reused(self):
        result = self.classifier.classify_candidate(candidate("https://www.anact.fr/themes/qvct", synthetic_only=False))
        self.assertFalse(result.synthetic_only)

    def test_candidate_rejection_is_preserved(self):
        value = replace(candidate("https://www.anact.fr/themes/qvct"), decision=FilterDecision.REJECTED, rejection_reason="duplicate_url")
        result = self.classifier.classify_candidate(value)
        self.assertEqual((ClassificationDecision.REJECTED, "duplicate_url"), (result.decision, result.rejection_reason))

    def test_candidate_batch_preserves_order(self):
        values = (candidate("https://www.anact.fr/themes/x"), candidate("https://www.anact.fr/actualites/y"))
        results = self.classifier.classify_candidates(values)
        self.assertEqual((UrlCategory.THEMATIC_PAGE, UrlCategory.NEWS), tuple(item.category for item in results))

    def test_no_fulltext_or_invented_fields(self):
        result = self.classifier.classify_url("https://www.anact.fr/publications/x")
        self.assertIsNone(result.fulltext)
        self.assertFalse(hasattr(result, "title"))
        self.assertFalse(hasattr(result, "author"))
        self.assertFalse(hasattr(result, "summary"))

    def test_contract_exposes_classifier(self):
        result = AnactConnector().classify_candidate(candidate("https://www.anact.fr/themes/x"))
        self.assertIs(UrlCategory.THEMATIC_PAGE, result.category)

    def test_contract_invariants_are_preserved(self):
        self.assertFalse(AnactConnector.enabled)
        self.assertEqual("architecture_only", AnactConnector.connector_status)
        self.assertIs(DocumentPolicy.METADATA_ONLY, AnactConnector.platform_contract.document_policy)
        self.assertIs(LicenseId.DOCUMENT_SPECIFIC, AnactConnector.platform_contract.license_id)

    def test_classifier_has_no_network_operation(self):
        source = inspect.getsource(AnactUrlClassifier)
        self.assertNotIn("urlopen", source)
        self.assertNotIn("requests", source)
        self.assertNotIn("httpx", source)


class AnactReviewQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.classifier = AnactUrlClassifier()
        self.queue = AnactReviewQueue()

    def test_add_and_deduplicate(self):
        result = self.classifier.classify_url("https://www.anact.fr/ressource/guide-qvct")
        self.assertTrue(self.queue.add(result))
        self.assertFalse(self.queue.add(result))
        self.assertEqual(1, len(self.queue.items()))

    def test_normalized_url_deduplicates_fragments(self):
        first = self.classifier.classify_url("https://www.anact.fr/themes/qvct#one")
        second = self.classifier.classify_url("https://www.anact.fr/themes/qvct#two")
        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertTrue(self.queue.add(first))
        self.assertFalse(self.queue.add(second))

    def test_priority_sorting(self):
        unknown = self.classifier.classify_url("https://www.anact.fr/inconnu")
        review = self.classifier.classify_url("https://www.anact.fr/ressource/guide-qvct")
        self.queue.add(unknown); self.queue.add(review)
        self.assertIs(review, self.queue.items()[0].classification)

    def test_explicit_priority(self):
        result = self.classifier.classify_url("https://www.anact.fr/inconnu")
        self.queue.add(result, priority=2)
        self.assertEqual(2, self.queue.items()[0].priority)

    def test_negative_priority_rejected(self):
        with self.assertRaises(ValueError): self.queue.add(self.classifier.classify_url("https://www.anact.fr/inconnu"), priority=-1)

    def test_filter_by_category(self):
        guide = self.classifier.classify_url("https://www.anact.fr/ressource/guide-qvct")
        unknown = self.classifier.classify_url("https://www.anact.fr/inconnu")
        self.queue.add(guide); self.queue.add(unknown)
        self.assertEqual((guide,), tuple(item.classification for item in self.queue.items(category=UrlCategory.GUIDE)))

    def test_filter_by_region(self):
        regional = self.classifier.classify_url("https://www.anact.fr/grand-est/ressource")
        self.queue.add(regional)
        self.assertEqual(1, len(self.queue.items(region_id="grand_est")))

    def test_accept_records_history(self):
        result = self.classifier.classify_url("https://www.anact.fr/inconnu")
        self.queue.add(result)
        item = self.queue.accept(result.fingerprint, "classification confirmée")
        self.assertEqual((HumanValidationStatus.ACCEPTED, 1), (item.status, len(item.history)))

    def test_reject_records_history(self):
        result = self.classifier.classify_url("https://www.anact.fr/inconnu")
        self.queue.add(result)
        item = self.queue.reject(result.fingerprint, "hors périmètre")
        self.assertIs(HumanValidationStatus.REJECTED, item.status)

    def test_recheck_records_ordered_history(self):
        result = self.classifier.classify_url("https://www.anact.fr/inconnu")
        self.queue.add(result)
        self.queue.accept(result.fingerprint, "première lecture")
        item = self.queue.request_recheck(result.fingerprint, "nouvelle vérification")
        self.assertEqual((1, 2), tuple(entry.sequence for entry in item.history))
        self.assertIs(HumanValidationStatus.RECHECK_REQUESTED, item.status)

    def test_filter_by_status(self):
        result = self.classifier.classify_url("https://www.anact.fr/inconnu")
        self.queue.add(result); self.queue.accept(result.fingerprint, "confirmé")
        self.assertEqual(1, len(self.queue.items(status=HumanValidationStatus.ACCEPTED)))

    def test_reason_is_required(self):
        result = self.classifier.classify_url("https://www.anact.fr/inconnu")
        self.queue.add(result)
        with self.assertRaises(ValueError): self.queue.accept(result.fingerprint, " ")

    def test_unknown_item_is_rejected(self):
        with self.assertRaises(KeyError): self.queue.reject("missing", "raison")

    def test_queue_is_in_memory_only(self):
        source = inspect.getsource(AnactReviewQueue)
        for primitive in ("open(", "write_text", "write_bytes", "sqlite"):
            self.assertNotIn(primitive, source)

    def test_contract_creates_empty_queue(self): self.assertFalse(AnactConnector().new_review_queue().items())


if __name__ == "__main__":
    unittest.main()
