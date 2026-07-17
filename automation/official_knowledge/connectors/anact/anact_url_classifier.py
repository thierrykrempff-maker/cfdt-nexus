"""Pure offline classifier for ANACT sitemap URL candidates."""
from urllib.parse import urlsplit

from .anact_classification_models import (
    ClassificationDecision,
    ClassificationRule,
    HumanValidationStatus,
    UrlCategory,
    UrlClassification,
)
from .anact_classification_rules import CLASSIFICATION_RULES, RULESET_VERSION
from .anact_models import ConfidenceLevel
from .anact_robots_policy import validate_candidate_url
from .anact_source_registry import REGION_BY_ID
from .anact_transport_models import FilterDecision, SitemapCandidate


class AnactUrlClassifier:
    def __init__(self, rules: tuple[ClassificationRule, ...] = CLASSIFICATION_RULES) -> None:
        self.rules = tuple(sorted(rules, key=lambda rule: (rule.priority, rule.rule_id)))

    def classify_candidate(self, candidate: SitemapCandidate) -> UrlClassification:
        if candidate.decision is FilterDecision.REJECTED:
            policy = validate_candidate_url(candidate.original_url)
            return UrlClassification.create(
                original_url=candidate.original_url,
                normalized_url=policy.normalized_url,
                category=UrlCategory.UNKNOWN_RESOURCE,
                confidence=ConfidenceLevel.VERY_HIGH,
                rule_id="sitemap_candidate_rejection",
                rule_version=RULESET_VERSION,
                justification="Le parseur sitemap a déjà rejeté cette entrée.",
                region_id=None,
                rejection_reason=candidate.rejection_reason or policy.reason or "candidate_rejected",
                decision=ClassificationDecision.REJECTED,
                human_validation_status=HumanValidationStatus.NOT_REQUIRED,
                synthetic_only=candidate.synthetic_only,
            )
        return self.classify_url(candidate.original_url, synthetic_only=candidate.synthetic_only)

    def classify_candidates(self, candidates: tuple[SitemapCandidate, ...]) -> tuple[UrlClassification, ...]:
        return tuple(self.classify_candidate(candidate) for candidate in candidates)

    def classify_url(self, url: str, *, synthetic_only: bool = True) -> UrlClassification:
        policy = validate_candidate_url(url)
        if not policy.allowed:
            return UrlClassification.create(
                original_url=url,
                normalized_url=None,
                category=UrlCategory.UNKNOWN_RESOURCE,
                confidence=ConfidenceLevel.VERY_HIGH,
                rule_id="url_policy_rejection",
                rule_version=RULESET_VERSION,
                justification="La politique URL/robots refuse cette ressource.",
                region_id=None,
                rejection_reason=policy.reason,
                decision=ClassificationDecision.REJECTED,
                human_validation_status=HumanValidationStatus.NOT_REQUIRED,
                synthetic_only=synthetic_only,
            )

        path = policy.path or "/"
        region_id = self._regional_entity(path)
        if region_id:
            return UrlClassification.create(
                original_url=url,
                normalized_url=policy.normalized_url,
                category=UrlCategory.REGIONAL_ARACT_PAGE,
                confidence=ConfidenceLevel.VERY_HIGH,
                rule_id="regional_registry_path",
                rule_version=RULESET_VERSION,
                justification="Le chemin appartient à une entité du registre régional ARACT.",
                region_id=region_id,
                rejection_reason=None,
                decision=ClassificationDecision.AUTO_ACCEPTED,
                human_validation_status=HumanValidationStatus.NOT_REQUIRED,
                synthetic_only=synthetic_only,
            )

        matches = tuple(rule for rule in self.rules if rule.matches(path))
        if not matches:
            return UrlClassification.create(
                original_url=url,
                normalized_url=policy.normalized_url,
                category=UrlCategory.UNKNOWN_RESOURCE,
                confidence=ConfidenceLevel.VERY_LOW,
                rule_id="no_reliable_rule",
                rule_version=RULESET_VERSION,
                justification="Aucune règle explicite ne classe ce chemin.",
                region_id=None,
                rejection_reason=None,
                decision=ClassificationDecision.UNCLASSIFIED,
                human_validation_status=HumanValidationStatus.PENDING,
                synthetic_only=synthetic_only,
            )

        best_priority = matches[0].priority
        best = tuple(rule for rule in matches if rule.priority == best_priority)
        categories = {rule.category for rule in best}
        if len(categories) > 1:
            identifiers = ",".join(rule.rule_id for rule in best)
            return UrlClassification.create(
                original_url=url,
                normalized_url=policy.normalized_url,
                category=UrlCategory.UNKNOWN_RESOURCE,
                confidence=ConfidenceLevel.MEDIUM,
                rule_id=f"conflict:{identifiers}",
                rule_version=RULESET_VERSION,
                justification="Plusieurs règles de même priorité produisent des catégories différentes.",
                region_id=None,
                rejection_reason=None,
                decision=ClassificationDecision.HUMAN_REVIEW_REQUIRED,
                human_validation_status=HumanValidationStatus.PENDING,
                synthetic_only=synthetic_only,
            )

        rule = best[0]
        certain = rule.confidence in {ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH}
        return UrlClassification.create(
            original_url=url,
            normalized_url=policy.normalized_url,
            category=rule.category,
            confidence=rule.confidence,
            rule_id=rule.rule_id,
            rule_version=rule.version,
            justification=rule.justification,
            region_id=None,
            rejection_reason=None,
            decision=ClassificationDecision.AUTO_ACCEPTED if certain else ClassificationDecision.HUMAN_REVIEW_REQUIRED,
            human_validation_status=HumanValidationStatus.NOT_REQUIRED if certain else HumanValidationStatus.PENDING,
            synthetic_only=synthetic_only,
        )

    @staticmethod
    def _regional_entity(path: str) -> str | None:
        normalized = path.rstrip("/") or "/"
        for region_id, entity in sorted(REGION_BY_ID.items()):
            root = urlsplit(entity.official_url).path.rstrip("/")
            if normalized == root or normalized.startswith(root + "/"):
                return region_id
        return None
