from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine, NOT_A_LEGAL_NORM
from tests.cse_cssct_test_support import corpus, pv_query, row
import json


def test_public_projection_has_no_internal_ids_or_paths(tmp_path):
    public = CSECSSCTSearchEngine(corpus(tmp_path)).search(
        pv_query("pause", "badgeage")
    ).to_dict(public=True)
    text = str(public)
    assert "source_path_hash" not in text
    assert "chunk_id" not in text
    assert "C:\\" not in text
    assert NOT_A_LEGAL_NORM in text


def test_public_excerpt_redacts_person_email_phone_and_local_path(tmp_path):
    root = corpus(tmp_path)
    extra = row(
        document_id="privacy",
        chunk_index=0,
        text=(
            "La direction informe Jean Dupont par jean.dupont@example.org au "
            "06 12 34 56 78 que le badgeage est décrit dans C:\\private\\pv.pdf."
        ),
    )
    with (root / "chunks" / "corpus.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(extra, ensure_ascii=False) + "\n")
    public = CSECSSCTSearchEngine(root).search(pv_query("badgeage")).to_dict(public=True)
    text = str(public)
    assert "Jean Dupont" not in text
    assert "example.org" not in text
    assert "06 12 34 56 78" not in text
    assert "private" not in text
