"""Unit tests for the agent search relevance scoring (functions/search/scorers.py).

These tests describe behaviour: real cosine distances map to a normalized
relevance score where a closer match scores higher. They do not assert the
internal formula.
"""

from search.scorers import compute_vec_scores


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
