"""Unit tests for the agent search target + shortfall behaviour.

Behaviour under test: the agent search honours a user-requested result count
and reports a shortfall when fewer ranked schemes exist than requested, so
the LLM can explain the gap rather than silently returning too few.
"""

import pandas as pd
import pytest
from search.handler import QueryHandler
from search.types import PaginatedSearchParams, PredictParams


@pytest.fixture
def handler(mocker):
    """A QueryHandler with the search model and persistence stubbed."""
    h = QueryHandler.__new__(QueryHandler)
    h.search_model = mocker.MagicMock()
    QueryHandler.firebase_manager = mocker.MagicMock()
    mocker.patch.object(h, "save_llm_query", return_value="doc-1")
    mocker.patch.object(h, "save_user_query", return_value=None)
    return h


def _ranked(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "scheme_id": [f"s{i}" for i in range(n)],
            "scheme": [f"S{i}" for i in range(n)],
            "combined_scores": [1.0 - (i * 0.01) for i in range(n)],
        }
    )


def test_predict_uses_top_k_as_requested_target(handler):
    handler.search_model.aggregate_and_rank_results.return_value = _ranked(3)

    handler.predict(PredictParams(query="education", top_k=5, is_warmup=True))

    handler.search_model.aggregate_and_rank_results.assert_called_once_with(
        "education",
        requested_target=5,
    )


def test_predict_paginated_uses_top_k_as_requested_target(handler):
    handler.search_model.aggregate_and_rank_results.return_value = _ranked(4)

    handler.predict_paginated(
        PaginatedSearchParams(
            query="education",
            limit=2,
            top_k=50,
            is_warmup=True,
        )
    )

    handler.search_model.aggregate_and_rank_results.assert_called_once_with(
        "education",
        requested_target=50,
    )


def test_reports_no_shortfall_when_target_met(handler):
    """User asked for 20, 20 ranked schemes exist -> no shortfall."""
    handler.search_model.aggregate_and_rank_results.return_value = _ranked(20)

    result = handler.predict_for_agent(PredictParams(query="healthcare", requested_target=20))

    assert len(result["data"]) == 20
    assert result["requested_target"] == 20
    assert result["shortfall"] is False
    handler.search_model.aggregate_and_rank_results.assert_called_once_with(
        "healthcare",
        requested_target=20,
    )


def test_reports_shortfall_when_fewer_ranked_schemes_than_requested(handler):
    """User asked for 100, only 40 ranked schemes exist -> shortfall."""
    handler.search_model.aggregate_and_rank_results.return_value = _ranked(40)

    result = handler.predict_for_agent(PredictParams(query="financial assistance", requested_target=100))

    assert len(result["data"]) == 40
    assert result["requested_target"] == 100
    assert result["shortfall"] is True


def test_no_target_is_not_a_shortfall(handler):
    """No requested count -> returning the ranked set is never a shortfall."""
    handler.search_model.aggregate_and_rank_results.return_value = _ranked(7)

    result = handler.predict_for_agent(PredictParams(query="help with bills"))

    assert len(result["data"]) == 7
    assert result["shortfall"] is False
    handler.search_model.aggregate_and_rank_results.assert_called_once_with(
        "help with bills",
        requested_target=None,
    )
