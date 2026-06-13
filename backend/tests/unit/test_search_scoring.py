"""Unit tests for the agent search relevance scoring (functions/search/scorers.py).

These tests describe behaviour: real cosine distances map to a normalized
relevance score where a closer match scores higher. They do not assert the
internal formula.
"""

import pandas as pd
from search.scorers import compute_bm25_scores, compute_rrf_scores, compute_vec_scores, rank_results


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


def test_bm25_uses_match_strength_not_just_rank_position():
    scores = compute_bm25_scores(
        "cash grant for household bills",
        [
            "cash grant household bills financial assistance cash grant",
            "cash support",
            "neighbourhood befriending activities",
        ],
    )

    assert scores[0] == 1.0
    assert scores[0] > scores[1]
    assert scores[0] > scores[2]


def test_rrf_fuses_vector_and_bm25_ranks():
    scores = compute_rrf_scores(
        vec_scores=[0.95, 0.80, 0.10],
        bm25_scores=[0.00, 1.00, 0.50],
    )

    assert scores[1] == 1.0
    assert scores[1] > scores[0]
    assert scores[1] > scores[2]
    assert all(0.0 <= score <= 1.0 for score in scores)


def test_rank_results_uses_rrf_combined_score():
    candidates = pd.DataFrame(
        [
            {
                "scheme_id": "strong",
                "search_booster": "cash, grant, household bills, financial assistance, cash grant",
                "vec_similarity_score": 0.5,
            },
            {
                "scheme_id": "weak",
                "search_booster": "cash support",
                "vec_similarity_score": 0.5,
            },
            {
                "scheme_id": "unrelated",
                "search_booster": "neighbourhood befriending activities",
                "vec_similarity_score": 0.5,
            },
        ]
    )

    ranked = rank_results("cash grant for household bills", candidates)
    bm25_scores = dict(zip(ranked["scheme_id"], ranked["bm25_score"]))

    assert ranked.iloc[0]["scheme_id"] == "strong"
    assert bm25_scores["strong"] == 1.0
    assert bm25_scores["strong"] > bm25_scores["weak"]
    assert ranked.iloc[0]["combined_scores"] == 1.0
