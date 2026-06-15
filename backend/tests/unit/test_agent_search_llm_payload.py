"""Unit tests for what the agent sends to the LLM vs the UI.

Behaviour under test: the UI receives the ranked scheme set (the user scrolls
and self-selects), but the LLM receives only the top-ranked slice with minimal
keys, to bound per-turn token cost. The slice is a pure, testable function.
"""

from search import LLM_RESULT_LIMIT, MINIMAL_LLM_KEYS, slim_for_llm


def _schemes(n):
    return [
        {
            "scheme_id": f"s{i}",
            "scheme": f"Scheme {i}",
            "agency": "A",
            "summary": "sum",
            "scraped_text": "huge blob that must not reach the LLM",
            "image": "x.jpg",
        }
        for i in range(n)
    ]


def test_llm_slice_is_capped_to_limit():
    """Far more ranked schemes than the LLM needs -> only the top slice goes."""
    slimmed = slim_for_llm(_schemes(200), LLM_RESULT_LIMIT)
    assert len(slimmed) == LLM_RESULT_LIMIT


def test_llm_slice_keeps_top_ranked_order():
    """The slice is the first N (ranking is already applied upstream)."""
    slimmed = slim_for_llm(_schemes(200), LLM_RESULT_LIMIT)
    assert [s["scheme_id"] for s in slimmed] == [f"s{i}" for i in range(LLM_RESULT_LIMIT)]


def test_llm_slice_drops_heavy_fields():
    """Only minimal keys reach the LLM; no scraped_text / image bloat."""
    slimmed = slim_for_llm(_schemes(3), LLM_RESULT_LIMIT)
    for s in slimmed:
        assert set(s.keys()) <= MINIMAL_LLM_KEYS
        assert "scraped_text" not in s


def test_llm_slice_returns_all_when_below_limit():
    """A small result set is returned whole."""
    slimmed = slim_for_llm(_schemes(5), LLM_RESULT_LIMIT)
    assert len(slimmed) == 5
