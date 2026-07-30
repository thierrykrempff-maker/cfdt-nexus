from SYNDICAL_REASONING_ENGINE import build_evidence_bundles, select_evidence
from tests.connector_execution_cases import plan_for
from tests.retrieval_propagation_support import summary_for


def test_sensitive_excerpt_is_never_selected_for_public_response():
    plan = plan_for()
    bundle = build_evidence_bundles(
        plan,
        summary_for(plan, sensitive=True, excerpt="information privée"),
    )[0]
    assert bundle.sensitive
    assert not bundle.usable_in_public_response
    assert not select_evidence((bundle,)).selected
    medical_bundle = build_evidence_bundles(
        plan,
        summary_for(
            plan,
            excerpt=(
                "Deux personnes ont été incommodées gastriquement avec présence de "
                "sang dans les selles. L’adéquation des EPI doit être vérifiée."
            ),
        ),
    )[0]
    assert "sang dans les selles" in medical_bundle.excerpt
    public_excerpt = medical_bundle.to_dict(public=True)["excerpt"]
    assert "sang" not in public_excerpt.casefold()
    assert "selles" not in public_excerpt.casefold()
    assert "EPI" in public_excerpt
