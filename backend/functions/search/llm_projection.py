"""Project search results down to what the agent's LLM should read.

The UI receives every relevant scheme (the user scrolls and self-selects); the
LLM only reads a top slice with minimal keys, which keeps its answer focused and
bounds per-turn token cost as the corpus grows. Pure functions, no framework
dependencies, so they're testable in isolation.
"""

# The only fields the LLM needs to reason about and cite a scheme. Heavy fields
# (scraped_text, images) are deliberately excluded.
MINIMAL_LLM_KEYS = {"scheme_id", "scheme", "agency", "summary"}


def slim_for_llm(schemes: list[dict], limit: int) -> list[dict]:
    """Take the top `limit` ranked schemes and keep only the minimal keys."""
    return [{k: v for k, v in scheme.items() if k in MINIMAL_LLM_KEYS} for scheme in schemes[:limit]]
