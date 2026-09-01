"""Unit tests for the BM25 re-ranking step (SearchModel.rank) in ml_logic.

This is the step that 500'd in production: it called the deprecated
`BM25Retriever.get_relevant_documents()`, which a `langchain-community` release
removed outright, so every real search raised AttributeError. The test exercises
the real retriever against the real langchain API, which is what makes it a
regression guard — a mocked retriever would have kept passing through the
removal. No embedding model or FAISS index is needed; `rank` only reads the
DataFrame it is handed.
"""

import pandas as pd
import pytest

from ml_logic.searchModelManager import SearchModel


@pytest.fixture
def model(mocker):
    mocker.patch.object(SearchModel, "initialise", return_value=None)
    SearchModel._instance = None
    SearchModel.initialised = True
    return SearchModel(mocker.MagicMock())


def _results() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "scheme_id": ["a", "b", "c"],
            "search_booster": [
                "childcare subsidy for preschool fees",
                "wheelchair mobility aid subsidy",
                "senior citizen transport concession",
            ],
            # Held equal so ordering is decided by the BM25 term alone.
            "vec_similarity_score": [0.5, 0.5, 0.5],
        }
    )


def test_rank_puts_the_bm25_match_first(model):
    ranked = model.rank("childcare preschool", _results())

    assert list(ranked["scheme_id"])[0] == "a"
    assert set(ranked["scheme_id"]) == {"a", "b", "c"}


def test_rank_combines_vector_and_bm25_weights(model):
    results = _results()
    ranked = model.rank("wheelchair mobility", results).set_index("scheme_id")

    # 0.7 * vector + 0.3 * bm25, and the best BM25 hit scores 1.0 at rank 0.
    assert ranked.loc["b", "bm25_score"] == pytest.approx(1.0)
    assert ranked.loc["b", "combined_scores"] == pytest.approx(0.7 * 0.5 + 0.3 * 1.0)
    # Every row keeps a combined score; a missing BM25 hit counts as zero.
    assert ranked["combined_scores"].notna().all()
    assert ranked["combined_scores"].min() >= 0.7 * 0.5


def test_rank_handles_blank_booster_text(model):
    results = _results()
    results.loc[0, "search_booster"] = None

    ranked = model.rank("childcare preschool", results)

    assert len(ranked) == 3
