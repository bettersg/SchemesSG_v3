"""Unit tests for relevance-driven result cutoff in aggregate_and_rank_results.

Behaviour under test: the agent search returns a *variable* number of schemes
driven by relevance, not a fixed count. Candidates below the relevance
threshold are dropped; the result is bounded by a safety cap. The vector
search itself is stubbed so these tests need no Firestore.
"""

import pandas as pd
import pytest

from search.retriever import SearchModel, SAFETY_CEILING, RELEVANCE_THRESHOLD


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
    the test isolates the *cutoff*, not the fusion maths.
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


def test_only_candidates_above_threshold_are_returned(model, mocker):
    """A narrow query where few clear the bar returns just those few."""
    mocker.patch.object(
        model,
        "search",
        return_value=_candidate_df({"a": 0.95, "b": 0.80, "c": 0.10, "d": 0.05}),
    )

    results = model.aggregate_and_rank_results("narrow query", RELEVANCE_THRESHOLD, None)

    kept = set(results["scheme_id"])
    assert kept == {"a", "b"}
    assert "c" not in kept and "d" not in kept


def test_no_target_returns_all_above_threshold(model, mocker):
    """A broad query with no requested count returns every relevant scheme."""
    scores = {f"s{i}": 0.9 for i in range(25)}  # 25 all clear the bar
    mocker.patch.object(model, "search", return_value=_candidate_df(scores))

    results = model.aggregate_and_rank_results("broad query", 0.5, None)

    assert len(results) == 25


def test_requested_target_caps_results(model, mocker):
    """When the user asks for N and more than N are relevant, return N."""
    scores = {f"s{i}": 0.9 for i in range(40)}  # 40 relevant
    mocker.patch.object(model, "search", return_value=_candidate_df(scores))

    results = model.aggregate_and_rank_results("healthcare", 0.5, requested_target=20)

    assert len(results) == 20


def test_relevance_floor_wins_over_target(model, mocker):
    """Asking for more than qualify returns only the qualifying ones, not padded."""
    scores = {"a": 0.9, "b": 0.8, "c": 0.7, "d": 0.1, "e": 0.05}  # only 3 clear 0.5
    mocker.patch.object(model, "search", return_value=_candidate_df(scores))

    results = model.aggregate_and_rank_results("rare topic", 0.5, requested_target=100)

    assert len(results) == 3  # never padded with the sub-threshold d, e


def test_safety_ceiling_caps_even_without_target(model, mocker):
    """A pathological all-relevant query is bounded by the safety ceiling."""
    scores = {f"s{i}": 0.9 for i in range(SAFETY_CEILING + 30)}
    mocker.patch.object(model, "search", return_value=_candidate_df(scores))

    results = model.aggregate_and_rank_results("everything", 0.5, None)

    assert len(results) == SAFETY_CEILING
