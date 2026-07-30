from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine
from tests.cse_cssct_test_support import corpus


def test_inventory_counts_real_prepared_shapes(tmp_path):
    inventory = CSECSSCTSearchEngine(corpus(tmp_path)).inventory()
    assert inventory.root_status == "AVAILABLE"
    assert inventory.document_count == 6
    assert inventory.indexable_chunk_count == 6
    assert dict(inventory.bodies) == {"CE": 1, "CSE": 4, "CSSCT": 1}
    assert inventory.cssct_distinguished is True


def test_missing_root_is_truthful(tmp_path):
    inventory = CSECSSCTSearchEngine(tmp_path / "absent").inventory()
    assert inventory.root_status == "UNAVAILABLE"
    assert inventory.document_count == 0
