from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine, NOT_A_LEGAL_NORM
import json

from tests.cse_cssct_test_support import corpus, pv_query, row


def test_minutes_never_replace_the_internal_procedure(tmp_path):
    root = corpus(tmp_path)
    misleading = row(
        document_id="messaging-procedure",
        chunk_index=0,
        text=(
            "La procédure de diffusion des messages électroniques est présentée. "
            "Les règles de messagerie seront communiquées aux utilisateurs."
        ),
    )
    with (root / "chunks" / "corpus.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(misleading, ensure_ascii=False) + "\n")
    result = CSECSSCTSearchEngine(root).search(
        pv_query("procédure", "instruction", "recette", "version", "diffusion")
    )
    assert result.results
    assert {item.document_id for item in result.results} == {"ce-procedure"}
    assert all(NOT_A_LEGAL_NORM in item.does_not_prove for item in result.results)
    assert all("procédure obligatoire" not in item.legal_value for item in result.results)
