"""Unit tests for the agent search relevance scoring (functions/search/scorers.py).

These tests describe behaviour: real cosine distances map to a normalized
relevance score where a closer match scores higher, and BM25 breaks ties between
equally-close candidates. They do not assert the internal formula.
"""

import pandas as pd
from search.scorers import compute_vec_scores, rank_results


def test_closer_distance_scores_higher():
    """A smaller cosine distance is a better match and must score higher."""
    ids = ["near", "far"]
    distances = [0.1, 0.9]  # cosine distance: 0 = identical, 2 = opposite

    df = compute_vec_scores(ids, distances)
    scores = dict(zip(df["scheme_id"], df["vec_similarity_score"]))

    assert scores["near"] > scores["far"]


def test_scores_are_normalized_zero_to_one():
    """Best match normalizes to 1, worst to 0, the rest in between."""
    df = compute_vec_scores(["a", "b", "c"], [0.2, 0.5, 1.4])
    scores = df["vec_similarity_score"].tolist()

    assert max(scores) == 1.0
    assert min(scores) == 0.0
    assert all(0.0 <= s <= 1.0 for s in scores)


def test_single_result_is_fully_relevant():
    """A lone match has nothing to normalize against and scores 1.0."""
    df = compute_vec_scores(["only"], [0.42])

    assert df["vec_similarity_score"].tolist() == [1.0]


def test_empty_input_returns_empty_frame():
    df = compute_vec_scores([], [])

    assert df.empty
    assert list(df.columns) == ["scheme_id", "vec_similarity_score"]


def test_bm25_breaks_ties_using_the_current_retriever_api():
    """BM25 decides the order when vector scores tie.

    A real ``BM25Retriever`` is used rather than a mock: LangChain removed
    ``get_relevant_documents()`` and a stale copy of this ranker kept calling it,
    which 500'd every ``schemes_search`` request (#410). A removed-API call has to
    fail here instead of in production.

    Two details keep the assertion honest. Three candidates, not two, because BM25
    floors the IDF of a term appearing in half the corpus and scores everything 0.
    And the query matches the *last* candidate, so a stable sort returning the input
    order fails — asserting against the first would pass even with BM25 contributing
    nothing.
    """
    tied_candidates = pd.DataFrame(
        {
            "scheme_id": ["housing", "healthcare", "education"],
            "search_booster": [
                "housing rental grant",
                "healthcare subsidy clinic",
                "school education bursary",
            ],
            "vec_similarity_score": [0.5, 0.5, 0.5],
        }
    )

    ranked = rank_results("school education bursary", tied_candidates)

    assert ranked["scheme_id"].tolist() == ["education", "healthcare", "housing"]
