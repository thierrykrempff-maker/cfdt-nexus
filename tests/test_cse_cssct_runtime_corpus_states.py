import json

from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine
from tests.cse_cssct_test_support import pv_query, row


def _write(root, name, values):
    chunks = root / "chunks"
    chunks.mkdir(parents=True, exist_ok=True)
    with (chunks / name).open("w", encoding="utf-8") as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False) + "\n")
    return root


def test_runtime_distinguishes_not_configured_from_missing_and_empty(tmp_path):
    assert CSECSSCTSearchEngine(None).inventory().root_status == "NOT_CONFIGURED"
    assert CSECSSCTSearchEngine(tmp_path / "missing").inventory().root_status == "UNAVAILABLE"
    empty = tmp_path / "empty"
    empty.mkdir()
    assert CSECSSCTSearchEngine(empty).inventory().root_status == "EMPTY"


def test_runtime_distinguishes_corrupt_jsonl(tmp_path):
    root = tmp_path / "corrupt"
    chunks = root / "chunks"
    chunks.mkdir(parents=True)
    (chunks / "broken.jsonl").write_text("{not-json\n", encoding="utf-8")
    inventory = CSECSSCTSearchEngine(root).inventory()
    assert inventory.root_status == "CORRUPT"
    assert inventory.load_error_count == 1


def test_runtime_marks_mixed_valid_and_corrupt_corpus_partial(tmp_path):
    root = _write(
        tmp_path / "partial",
        "valid.jsonl",
        [row(document_id="valid", chunk_index=0, text="Les élus demandent un suivi précis.")],
    )
    (root / "chunks" / "broken.jsonl").write_text("{not-json\n", encoding="utf-8")
    inventory = CSECSSCTSearchEngine(root).inventory()
    assert inventory.root_status == "PARTIAL"
    assert inventory.indexable_document_count == 1
    assert inventory.load_error_count == 1


def test_runtime_marks_empty_document_and_incomplete_metadata_partial(tmp_path):
    empty_row = row(document_id="empty", chunk_index=0, text="", indexable=False)
    incomplete_row = row(
        document_id="incomplete",
        chunk_index=0,
        text="Les élus demandent un suivi documenté de la consultation.",
    )
    incomplete_row["metadata_snapshot"] = {}
    root = _write(tmp_path / "partial", "corpus.jsonl", [empty_row, incomplete_row])
    inventory = CSECSSCTSearchEngine(root).inventory()
    assert inventory.root_status == "PARTIAL"
    assert inventory.empty_documents == 1
    assert inventory.incomplete_metadata_documents == 1


def test_public_projection_distinguishes_all_runtime_states(tmp_path):
    roots = {
        "NOT_CONFIGURED": None,
        "UNAVAILABLE": tmp_path / "missing",
        "EMPTY": tmp_path / "empty",
    }
    roots["EMPTY"].mkdir()
    for expected, root in roots.items():
        execution = CSECSSCTSearchEngine(root).search(pv_query("pause", "badgeage"))
        public = execution.to_dict(public=True)
        assert public["corpus_status"] == expected
        assert public["search_executed"] is False
        assert public["message"]


def test_partial_corpus_remains_searchable_and_truthfully_labelled(tmp_path):
    root = _write(
        tmp_path / "partial",
        "corpus.jsonl",
        [
            row(
                document_id="partial",
                chunk_index=0,
                text=(
                    "Les élus demandent comment sont décomptées les pauses. "
                    "La direction répond que le badgeage doit être vérifié."
                ),
            ),
            row(document_id="empty", chunk_index=0, text="", indexable=False),
        ],
    )
    execution = CSECSSCTSearchEngine(root).search(pv_query("pause", "badgeage"))
    public = execution.to_dict(public=True)
    assert execution.corpus_root_status == "PARTIAL"
    assert public["search_executed"] is True
    assert public["results_retained"] == 1
    assert "partiellement exploitable" in " ".join(public["corpus_limits"]).lower()
