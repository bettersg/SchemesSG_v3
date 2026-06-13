"""Unit tests for dynamic ranked result cutoff in aggregate_and_rank_results.

Behaviour under test: search returns a dynamically cut ranked prefix unless the
user explicitly asks for a count. The vector search itself is stubbed so these
tests need no Firestore.
"""

import pandas as pd
import pytest
from search.retriever import DEFAULT_MAX_RESULTS, DEFAULT_MIN_RESULTS, SearchModel, apply_elbow_cutoff


def _candidate_df(scores: dict[str, float]) -> pd.DataFrame:
    """Build a candidate frame shaped like SearchModel.search output."""
    return pd.DataFrame(
        {
            "scheme_id": list(scores.keys()),
            "vec_similarity_score": list(scores.values()),
            "search_booster": ["" for _ in scores],
            "query": ["q" for _ in scores],
        }
    )


@pytest.fixture
def model(mocker):
    """A SearchModel with vector search and BM25 ranking stubbed out.

    rank() is stubbed to pass vec scores straight through as combined_scores so
    the test isolates result count, not the fusion maths.
    """
    mocker.patch.object(SearchModel, "initialise", return_value=None)
    SearchModel._instance = None
    SearchModel.initialised = True
    m = SearchModel(mocker.MagicMock())

    def fake_rank(query_text, results):
        out = results.copy()
        out["combined_scores"] = out["vec_similarity_score"]
        return out.sort_values("combined_scores", ascending=False)

    mocker.patch.object(m, "rank", side_effect=fake_rank)
    m.query_cache = {}
    return m


def test_elbow_cutoff_keeps_at_least_minimum_then_cuts_on_score_drop():
    scores = [0.95 - (i * 0.01) for i in range(DEFAULT_MIN_RESULTS)]
    scores.extend([0.70, 0.69, 0.68])
    ranked = pd.DataFrame(
        {
            "scheme_id": [f"s{i}" for i in range(len(scores))],
            "combined_scores": scores,
        }
    )

    results = apply_elbow_cutoff(ranked)

    assert len(results) == DEFAULT_MIN_RESULTS
    assert results["scheme_id"].tolist() == [f"s{i}" for i in range(DEFAULT_MIN_RESULTS)]


def test_no_elbow_returns_bounded_ranked_prefix(model, mocker):
    """Without a clear elbow, return a bounded prefix instead of 300 results."""
    scores = {f"s{i}": 1.0 - (i * 0.001) for i in range(DEFAULT_MAX_RESULTS + 30)}
    mocker.patch.object(model, "search", return_value=_candidate_df(scores))

    results = model.aggregate_and_rank_results("smooth broad query")

    assert len(results) == DEFAULT_MAX_RESULTS


def test_requested_target_caps_results(model, mocker):
    """When the user asks for N, return the top N ranked candidates."""
    scores = {f"s{i}": 1.0 - (i * 0.01) for i in range(40)}
    mocker.patch.object(model, "search", return_value=_candidate_df(scores))

    results = model.aggregate_and_rank_results("healthcare", requested_target=20)

    assert len(results) == 20


def test_small_result_set_returns_all_results(model, mocker):
    """If fewer than the minimum exist, return them all."""
    scores = {"a": 0.9, "b": 0.7, "c": 0.1, "d": 0.05}
    mocker.patch.object(model, "search", return_value=_candidate_df(scores))

    results = model.aggregate_and_rank_results("small query")

    assert len(results) == 4
    assert results["scheme_id"].tolist() == ["a", "b", "c", "d"]
