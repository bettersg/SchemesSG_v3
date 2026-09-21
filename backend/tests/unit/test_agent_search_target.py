"""Unit tests for the agent search target + shortfall behaviour.

Behaviour under test: the agent search honours a user-requested result count
and reports a shortfall when fewer relevant schemes exist than requested, so
the LLM can explain the gap rather than silently returning too few.
"""

import pandas as pd
import pytest

from search.handler import QueryHandler
from search.types import PredictParams


@pytest.fixture
def handler(mocker):
    """A QueryHandler with the search model and persistence stubbed."""
    h = QueryHandler.__new__(QueryHandler)
    h.search_model = mocker.MagicMock()
    QueryHandler.firebase_manager = mocker.MagicMock()
    mocker.patch.object(h, "save_llm_query", return_value="doc-1")
    return h


def _ranked(n: int) -> pd.DataFrame:
    return pd.DataFrame({"scheme_id": [f"s{i}" for i in range(n)], "scheme": [f"S{i}" for i in range(n)]})


def test_reports_no_shortfall_when_target_met(handler):
    """User asked for 20, 20 relevant exist -> no shortfall."""
    handler.search_model.aggregate_and_rank_results.return_value = _ranked(20)

    result = handler.predict_for_agent(PredictParams(query="healthcare", requested_target=20))

    assert len(result["data"]) == 20
    assert result["requested_target"] == 20
    assert result["shortfall"] is False


def test_reports_shortfall_when_fewer_relevant_than_requested(handler):
    """User asked for 100, only 40 clear the relevance floor -> shortfall."""
    handler.search_model.aggregate_and_rank_results.return_value = _ranked(40)

    result = handler.predict_for_agent(PredictParams(query="financial assistance", requested_target=100))

    assert len(result["data"]) == 40
    assert result["requested_target"] == 100
    assert result["shortfall"] is True


def test_no_target_is_not_a_shortfall(handler):
    """No requested count -> returning whatever is relevant is never a shortfall."""
    handler.search_model.aggregate_and_rank_results.return_value = _ranked(7)

    result = handler.predict_for_agent(PredictParams(query="help with bills"))

    assert len(result["data"]) == 7
    assert result["shortfall"] is False
